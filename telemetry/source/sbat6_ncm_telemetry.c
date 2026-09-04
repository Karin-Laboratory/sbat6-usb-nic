// SPDX-License-Identifier: GPL-2.0
/*
 * T6A NCM telemetry core for Linux 5.4.
 *
 * This module intentionally has no kprobes, ftrace hooks, USB registration,
 * configfs access, UDC access, netdev access, timers, or workqueues.  It is a
 * counter sink for a separately reviewed vendor-tree instrumentation patch.
 * Until that patch calls these exported functions, all values remain zero.
 */
#include <linux/debugfs.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/percpu.h>
#include <linux/seq_file.h>
#include <linux/smp.h>
#include <linux/ktime.h>
#include <linux/uaccess.h>

#define SBAT6_LAT_BINS 12
#define SBAT6_LAT_STEP_NS 1000ULL

struct sbat6_cpu_stats {
	u64 tx_ntb, tx_payload, tx_capacity, tx_frames;
	u64 tx_flush, tx_full, tx_queued, tx_completed, tx_queue_fail, tx_retry;
	u64 tx_latency_ns, tx_latency_n;
	u64 rx_ntb, rx_payload, rx_datagrams, rx_unwrap, rx_skb_alloc;
	u64 rx_unwrap_ns, rx_unwrap_n, rx_malformed, rx_drop, rx_error;
	u64 rx_completed;
	u64 tx_inflight_sum, tx_inflight_samples, rx_inflight_sum, rx_inflight_samples;
	u64 tx_completion_interval_ns, tx_completion_interval_n;
	u64 rx_completion_interval_ns, rx_completion_interval_n;
	u64 irq, dma_map, starvation, empty, full, nak, idle_ns;
	u64 tx_lat_hist[SBAT6_LAT_BINS], rx_lat_hist[SBAT6_LAT_BINS];
	u64 tx_gap_hist[SBAT6_LAT_BINS], rx_gap_hist[SBAT6_LAT_BINS];
	ktime_t last_tx_completion, last_rx_completion;
};

static DEFINE_PER_CPU(struct sbat6_cpu_stats, sbat6_stats);
static struct dentry *sbat6_dir;

static unsigned int sbat6_bin(u64 ns)
{
	unsigned int b = 0;

	while (ns >= SBAT6_LAT_STEP_NS && b < SBAT6_LAT_BINS - 1) {
		ns >>= 1;
		b++;
	}
	return b;
}

static void sbat6_interval(u64 *sum, u64 *count, u64 *hist, ktime_t *last)
{
	ktime_t now = ktime_get();

	if (*last) {
		u64 ns = ktime_to_ns(ktime_sub(now, *last));
		*sum += ns;
		(*count)++;
		hist[sbat6_bin(ns)]++;
	}
	*last = now;
}

/* Called by a reviewed TX path at NTB handoff to usb_ep_queue(). */
void sbat6_ncm_tx_ntb(unsigned int payload, unsigned int capacity,
			      unsigned int frames, bool flush, bool full)
{
	struct sbat6_cpu_stats *s = this_cpu_ptr(&sbat6_stats);

	s->tx_ntb++;
	s->tx_payload += payload;
	s->tx_capacity += capacity;
	s->tx_frames += frames;
	s->tx_flush += flush;
	s->tx_full += full;
}
EXPORT_SYMBOL_GPL(sbat6_ncm_tx_ntb);

void sbat6_ncm_tx_queue(bool success, bool retry, unsigned int inflight)
{
	struct sbat6_cpu_stats *s = this_cpu_ptr(&sbat6_stats);

	s->tx_queued += success;
	s->tx_queue_fail += !success;
	s->tx_retry += retry;
	s->tx_inflight_sum += inflight;
	s->tx_inflight_samples++;
}
EXPORT_SYMBOL_GPL(sbat6_ncm_tx_queue);

void sbat6_ncm_tx_complete(unsigned int latency_us, unsigned int gap_us,
				   bool timestamp_valid)
{
	struct sbat6_cpu_stats *s = this_cpu_ptr(&sbat6_stats);
	u64 ns = (u64)latency_us * 1000ULL;
	u64 gap_ns = (u64)gap_us * 1000ULL;

	s->tx_completed++;
	if (timestamp_valid) {
		s->tx_latency_ns += ns;
		s->tx_latency_n++;
		s->tx_lat_hist[sbat6_bin(ns)]++;
		if (gap_us) {
			s->tx_completion_interval_ns += gap_ns;
			s->tx_completion_interval_n++;
			s->tx_gap_hist[sbat6_bin(gap_ns)]++;
		}
	}
}
EXPORT_SYMBOL_GPL(sbat6_ncm_tx_complete);

void sbat6_ncm_rx_ntb(unsigned int payload, unsigned int datagrams)
{
	struct sbat6_cpu_stats *s = this_cpu_ptr(&sbat6_stats);

	s->rx_ntb++;
	s->rx_payload += payload;
	s->rx_datagrams += datagrams;
}
EXPORT_SYMBOL_GPL(sbat6_ncm_rx_ntb);

void sbat6_ncm_rx_unwrap(unsigned int unwraps, unsigned int skb_allocs,
				 unsigned int elapsed_us)
{
	struct sbat6_cpu_stats *s = this_cpu_ptr(&sbat6_stats);

	s->rx_unwrap += unwraps;
	s->rx_skb_alloc += skb_allocs;
	s->rx_unwrap_ns += (u64)elapsed_us * 1000ULL;
	s->rx_unwrap_n++;
}
EXPORT_SYMBOL_GPL(sbat6_ncm_rx_unwrap);

void sbat6_ncm_rx_complete(unsigned int inflight)
{
	struct sbat6_cpu_stats *s = this_cpu_ptr(&sbat6_stats);

	s->rx_completed++;
	s->rx_inflight_sum += inflight;
	s->rx_inflight_samples++;
	sbat6_interval(&s->rx_completion_interval_ns,
			       &s->rx_completion_interval_n, s->rx_gap_hist,
			       &s->last_rx_completion);
}
EXPORT_SYMBOL_GPL(sbat6_ncm_rx_complete);

void sbat6_ncm_rx_error(bool malformed, bool drop, bool error)
{
	struct sbat6_cpu_stats *s = this_cpu_ptr(&sbat6_stats);

	s->rx_malformed += malformed;
	s->rx_drop += drop;
	s->rx_error += error;
}
EXPORT_SYMBOL_GPL(sbat6_ncm_rx_error);

void sbat6_ncm_mtu3_event(unsigned int irq, unsigned int dma_map,
				  unsigned int starvation, unsigned int empty,
				  unsigned int full, unsigned int nak,
				  unsigned int idle_us)
{
	struct sbat6_cpu_stats *s = this_cpu_ptr(&sbat6_stats);

	s->irq += irq;
	s->dma_map += dma_map;
	s->starvation += starvation;
	s->empty += empty;
	s->full += full;
	s->nak += nak;
	s->idle_ns += (u64)idle_us * 1000ULL;
}
EXPORT_SYMBOL_GPL(sbat6_ncm_mtu3_event);

#define SUM_FIELD(name) do { int cpu; for_each_possible_cpu(cpu) total += per_cpu(sbat6_stats, cpu).name; } while (0)

static void sbat6_print_sum(struct seq_file *m, const char *name, u64 total)
{
	seq_printf(m, "%s=%llu\n", name, (unsigned long long)total);
}

static int sbat6_stats_show(struct seq_file *m, void *unused)
{
	u64 total;

#define OUT(field) do { total = 0; SUM_FIELD(field); sbat6_print_sum(m, #field, total); } while (0)
	OUT(tx_ntb); OUT(tx_payload); OUT(tx_capacity); OUT(tx_frames);
	OUT(tx_flush); OUT(tx_full); OUT(tx_queued); OUT(tx_completed);
	OUT(tx_queue_fail); OUT(tx_retry); OUT(tx_latency_ns); OUT(tx_latency_n);
	OUT(rx_ntb); OUT(rx_payload); OUT(rx_datagrams); OUT(rx_unwrap);
	OUT(rx_skb_alloc); OUT(rx_unwrap_ns); OUT(rx_unwrap_n);
	OUT(rx_malformed); OUT(rx_drop); OUT(rx_error); OUT(rx_completed);
	OUT(tx_inflight_sum); OUT(tx_inflight_samples);
	OUT(rx_inflight_sum); OUT(rx_inflight_samples);
	OUT(tx_completion_interval_ns); OUT(tx_completion_interval_n);
	OUT(rx_completion_interval_ns); OUT(rx_completion_interval_n);
	OUT(irq); OUT(dma_map); OUT(starvation); OUT(empty); OUT(full);
	OUT(nak); OUT(idle_ns);
#undef OUT
	seq_printf(m, "possible_cpus=%u\n", num_possible_cpus());
	seq_printf(m, "latency_bins_ns=1000,2000,4000,8000,16000,32000,64000,128000,256000,512000,1024000,or-more\n");
	return 0;
}

static int sbat6_stats_open(struct inode *inode, struct file *file)
{
	return single_open(file, sbat6_stats_show, inode->i_private);
}

static const struct file_operations sbat6_stats_fops = {
	.owner = THIS_MODULE,
	.open = sbat6_stats_open,
	.read = seq_read,
	.llseek = seq_lseek,
	.release = single_release,
};

static int __init sbat6_telemetry_init(void)
{
	sbat6_dir = debugfs_create_dir("sbat6_ncm_telemetry", NULL);
	if (!sbat6_dir)
		return -ENOMEM;
	if (!debugfs_create_file("stats", 0444, sbat6_dir, NULL,
				 &sbat6_stats_fops)) {
		debugfs_remove_recursive(sbat6_dir);
		sbat6_dir = NULL;
		return -ENOMEM;
	}
	pr_info("sbat6_ncm_telemetry: counter sink ready; no USB hooks installed\n");
	return 0;
}

static void __exit sbat6_telemetry_exit(void)
{
	debugfs_remove_recursive(sbat6_dir);
	pr_info("sbat6_ncm_telemetry: removed; no USB state changed\n");
}

module_init(sbat6_telemetry_init);
module_exit(sbat6_telemetry_exit);
MODULE_DESCRIPTION("T6A NCM telemetry counter sink; no automatic hooks");
MODULE_LICENSE("GPL");
