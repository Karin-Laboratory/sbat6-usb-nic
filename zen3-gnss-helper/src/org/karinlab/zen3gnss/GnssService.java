package org.karinlab.zen3gnss;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.GnssClock;
import android.location.GnssMeasurementsEvent;
import android.location.GnssStatus;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.IBinder;
import android.os.SystemClock;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/** GNSS status sender. Framework registrations and sender resources have one owner. */
public final class GnssService extends Service {
  private static final String TAG = "GnssService";
  private static final String CHANNEL = "zen3-gnss";
  private static final int PORT = 40123;
  private static final String BROADCAST = "192.168.3.255";
  private static final String MARKER = "zen3-gnss-v1-7f3c9a";
  private static final double GPS_EPOCH_UNIX_S = 315964800.0;
  private static final double GPS_UTC_LEAP_SECONDS = 18.0;
  private static final long SEND_STALE_MS = 25000;
  private final Object lock = new Object();
  private LocationManager lm;
  private LocationListener locationListener;
  private GnssStatus.Callback statusCallback;
  private GnssMeasurementsEvent.Callback measurementsCallback;
  private SenderSession sender;
  private ScheduledExecutorService watchdog;
  private volatile boolean destroying;
  private volatile long lastFixElapsed;
  private volatile long lastSendElapsed;
  private volatile int satellites;
  private volatile float meanCn0;
  private volatile double utcSeconds;
  private volatile long nextRecoveryElapsed;
  private volatile int recoveryCount;
  private volatile int sentPackets;
  private volatile int consecutiveSuccessfulSends;
  private volatile long lastRecoveryElapsed;
  private static final int SUCCESSFUL_SENDS_TO_RESET = 30;
  private static final long STABLE_NORMAL_MS = 120000;

  /** The session, its thread, and its socket form one ownership unit. */
  private final class SenderSession {
    final Thread thread;
    volatile DatagramSocket socket;
    volatile boolean stopRequested;
    SenderSession() { thread = new Thread(() -> sendLoop(this), "gnss-sender"); }
    void requestStop() {
      stopRequested = true;
      thread.interrupt();
      DatagramSocket s = socket;
      if (s != null) s.close();
    }
  }

  public static void start(Context c) {
    Intent i = new Intent(c, GnssService.class);
    if (Build.VERSION.SDK_INT >= 26) c.startForegroundService(i); else c.startService(i);
  }

  @Override public void onCreate() {
    super.onCreate(); logI("service create");
    NotificationManager nm = getSystemService(NotificationManager.class);
    if (Build.VERSION.SDK_INT >= 26) nm.createNotificationChannel(new NotificationChannel(CHANNEL, "GNSS", NotificationManager.IMPORTANCE_LOW));
    startForeground(1, new Notification.Builder(this, CHANNEL).setContentTitle("Zen3 GNSS Helper")
        .setContentText("GNSS status feeder active").setSmallIcon(android.R.drawable.ic_menu_mylocation).setOngoing(true).build());
    lm = (LocationManager)getSystemService(LOCATION_SERVICE);
    if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) { logE("location permission missing", null); return; }
    registerCallbacks();
    startSender("service-create");
    watchdog = Executors.newSingleThreadScheduledExecutor(r -> new Thread(r, "gnss-watchdog"));
    watchdog.scheduleWithFixedDelay(this::watchdog, 5000, 5000, TimeUnit.MILLISECONDS);
  }

  private void registerCallbacks() {
    synchronized (lock) {
      if (locationListener != null || statusCallback != null || measurementsCallback != null) { logI("duplicate-start suppression: callbacks already registered"); return; }
      locationListener = new LocationListener() {
        @Override public void onLocationChanged(Location l) { lastFixElapsed = l.getElapsedRealtimeNanos(); utcSeconds = l.getTime() / 1000.0; logD("GNSS location callback"); }
      };
      statusCallback = new GnssStatus.Callback() {
        @Override public void onSatelliteStatusChanged(GnssStatus s) { int n=0; float sum=0; for (int i=0;i<s.getSatelliteCount();i++) if (s.usedInFix(i)) { n++; sum+=s.getCn0DbHz(i); } satellites=n; meanCn0=n==0?0:sum/n; logD("GNSS status callback satellites="+n); }
      };
      measurementsCallback = new GnssMeasurementsEvent.Callback() {
        @Override public void onGnssMeasurementsReceived(GnssMeasurementsEvent e) { GnssClock c=e.getClock(); if (!c.hasFullBiasNanos()) return; long bias=c.getFullBiasNanos(); double b=c.hasBiasNanos()?c.getBiasNanos():0.0; utcSeconds=(c.getTimeNanos()-(bias+b))/1e9+GPS_EPOCH_UNIX_S-GPS_UTC_LEAP_SECONDS; logD("GNSS measurement callback"); }
      };
      try {
        lm.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000, 0, locationListener); logI("location listener register");
        if (!lm.registerGnssStatusCallback(statusCallback)) throw new IllegalStateException("status registration rejected"); logI("GNSS status callback register");
        if (!lm.registerGnssMeasurementsCallback(measurementsCallback)) throw new IllegalStateException("measurement registration rejected"); logI("GNSS measurement callback register");
      } catch (RuntimeException e) { logE("callback registration exception", e); unregisterCallbacksLocked(); }
    }
  }

  private void unregisterCallbacksLocked() {
    if (lm == null) return;
    if (locationListener != null) { try { lm.removeUpdates(locationListener); } catch (RuntimeException e) { logE("location unregister exception", e); } logI("location listener unregister"); }
    if (statusCallback != null) { try { lm.unregisterGnssStatusCallback(statusCallback); } catch (RuntimeException e) { logE("status unregister exception", e); } logI("GNSS status callback unregister"); }
    if (measurementsCallback != null) { try { lm.unregisterGnssMeasurementsCallback(measurementsCallback); } catch (RuntimeException e) { logE("measurement unregister exception", e); } logI("GNSS measurement callback unregister"); }
    locationListener=null; statusCallback=null; measurementsCallback=null;
  }

  private void startSender(String reason) {
    synchronized (lock) {
      if (destroying) return;
      if (sender != null && sender.thread.isAlive()) { logI("duplicate-start suppression: sender alive"); return; }
      sender = new SenderSession(); sender.thread.start(); logI("sender start reason="+reason);
    }
  }
  private void stopSenderAndWait(String reason) {
    SenderSession old;
    synchronized (lock) { old=sender; sender=null; }
    if (old == null) return;
    old.requestStop();
    if (Thread.currentThread() != old.thread) try { old.thread.join(); }
    catch (InterruptedException e) { Thread.currentThread().interrupt(); logE("sender join interrupted", e); }
    logI("sender thread stopped reason="+reason+" alive="+old.thread.isAlive());
  }
  private void restartSender(String reason) { stopSenderAndWait(reason); startSender(reason); }

  private void sendLoop(SenderSession session) {
    DatagramSocket s=null;
    try {
      s=new DatagramSocket(); session.socket=s;
      synchronized(lock) { if (destroying || session.stopRequested || sender != session) return; }
      s.setBroadcast(true); InetAddress dst=InetAddress.getByName(BROADCAST); logI("UDP socket open destination="+BROADCAST+":"+PORT);
      while (!Thread.currentThread().isInterrupted() && !destroying && !session.stopRequested) {
        long now=SystemClock.elapsedRealtime(); double age=lastFixElapsed==0?9999:(SystemClock.elapsedRealtimeNanos()-lastFixElapsed)/1e9;
        boolean valid=utcSeconds>1700000000 && age<10 && satellites>=4;
        String msg=String.format(Locale.US,"{\"marker\":\"%s\",\"v\":1,\"valid\":%s,\"utc_unix_s\":%.9f,\"fix_age_s\":%.3f,\"satellites\":%d,\"mean_cn0\":%.1f}",MARKER,valid,utcSeconds,age,satellites,meanCn0);
        byte[] data=msg.getBytes(StandardCharsets.US_ASCII); s.send(new DatagramPacket(data,data.length,dst,PORT)); lastSendElapsed=now; sentPackets++; consecutiveSuccessfulSends++;
        logD("UDP send success destination="+BROADCAST+":"+PORT+" count="+sentPackets);
        if (sentPackets%15==0) logI(String.format(Locale.US,"health fix_age=%.1f satellites=%d last_send_age=0 recovery_count=%d",age,satellites,recoveryCount));
        Thread.sleep(2000);
      }
    } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    catch (Exception e) { logE("UDP send failure", e); }
    finally { if (s!=null) { s.close(); session.socket=null; logI("UDP socket close owner="+session.thread.getName()); } }
  }

  private void watchdog() {
    if (destroying) return; long now=SystemClock.elapsedRealtime(); long fixAge=lastFixElapsed==0?Long.MAX_VALUE:(SystemClock.elapsedRealtimeNanos()-lastFixElapsed)/1000000L; long sendAge=lastSendElapsed==0?Long.MAX_VALUE:now-lastSendElapsed;
    if (recoveryCount>0 && (consecutiveSuccessfulSends>=SUCCESSFUL_SENDS_TO_RESET || now-lastRecoveryElapsed>=STABLE_NORMAL_MS)) {
      logI("watchdog backoff reset reason=" + (consecutiveSuccessfulSends>=SUCCESSFUL_SENDS_TO_RESET ? "stable-successful-udp-sends" : "stable-normal-period"));
      recoveryCount=0; nextRecoveryElapsed=0; consecutiveSuccessfulSends=0;
    }
    if (fixAge<10000 && sendAge>SEND_STALE_MS && now>=nextRecoveryElapsed) {
      recoveryCount++; long backoff=Math.min(600000L,60000L<<Math.min(recoveryCount-1,3)); nextRecoveryElapsed=now+backoff;
      lastRecoveryElapsed=now; consecutiveSuccessfulSends=0;
      logI("watchdog recovery count="+recoveryCount+" fix_age_ms="+fixAge+" send_age_ms="+sendAge); restartSender("watchdog");
    }
  }

  @Override public int onStartCommand(Intent i,int flags,int id) { logI("service start id="+id); registerCallbacks(); startSender("start-command"); return START_STICKY; }
  @Override public void onDestroy() { destroying=true; logI("service destroy"); if (watchdog!=null) watchdog.shutdownNow(); synchronized(lock) { unregisterCallbacksLocked(); } stopSenderAndWait("destroy"); super.onDestroy(); }
  @Override public IBinder onBind(Intent i) { return null; }
  private static void logI(String s) { android.util.Log.i(TAG,s); }
  private static void logD(String s) { android.util.Log.d(TAG,s); }
  private static void logE(String s, Throwable t) { android.util.Log.e(TAG,s,t); }
}
