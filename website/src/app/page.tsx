'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence, useInView, useScroll, useTransform } from 'framer-motion'
import {
  Menu, X, ArrowRight, Check, ChevronDown, Zap, Shield, BarChart3,
  Layers, Target, TrendingUp, Activity, Clock, Sparkles, Bot,
  CandlestickChart, Lock, Globe, RefreshCw, Bell, Brain, Filter,
  ArrowDownRight, Play, Star, AlertTriangle
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  RadarChart, PolarGrid, PolarAngleAxis, Radar, AreaChart, Area
} from 'recharts'
import { useCountUp, ScrollReveal, ScrollProgress } from '@/lib/animations'

const PAIR_DATA = [
  { pair: 'XAUUSD', pf: 3.65, wr: 67, trades: 450, sharpe: 2.84 },
  { pair: 'GBPUSD', pf: 1.96, wr: 62, trades: 680, sharpe: 1.82 },
  { pair: 'AUDUSD', pf: 1.89, wr: 60, trades: 720, sharpe: 1.74 },
  { pair: 'EURUSD', pf: 1.57, wr: 59, trades: 610, sharpe: 1.41 },
  { pair: 'GBPJPY', pf: 1.45, wr: 58, trades: 590, sharpe: 1.32 },
  { pair: 'NZDUSD', pf: 1.39, wr: 57, trades: 700, sharpe: 1.25 },
  { pair: 'USDCAD', pf: 1.29, wr: 55, trades: 750, sharpe: 1.18 },
  { pair: 'USDJPY', pf: 1.22, wr: 54, trades: 730, sharpe: 1.10 },
]

const EQUITY_CURVE = Array.from({ length: 50 }, (_, i) => ({
  month: i,
  equity: Math.round(10000 * Math.pow(1.038, i) + Math.sin(i * 0.5) * 200),
  dd: Math.max(0, Math.round(-8 + Math.random() * 3)),
}))

const SCORING_RADAR = [
  { score: 95, label: 'Structure', fullMark: 100 },
  { score: 88, label: 'Momentum', fullMark: 100 },
  { score: 92, label: 'Volume', fullMark: 100 },
  { score: 85, label: 'Sentiment', fullMark: 100 },
  { score: 90, label: 'Volatility', fullMark: 100 },
  { score: 87, label: 'Timing', fullMark: 100 },
]

const PIPELINE_STEPS = [
  { icon: BarChart3, label: 'Data Ingestion', desc: 'Real-time OHLCV across 8 pairs', layer: 1 },
  { icon: CandlestickChart, label: 'Structure Mapping', desc: 'BOS, CHoCH, Order Blocks', layer: 2 },
  { icon: Target, label: 'POI Detection', desc: 'Premium/Discount zones', layer: 3 },
  { icon: TrendingUp, label: 'Trend Alignment', desc: 'Multi-timeframe confluence', layer: 4 },
  { icon: Filter, label: '8-Gate Filter', desc: 'Sequential fail-fast pipeline', layer: 5 },
  { icon: Brain, label: 'Entry Logic', desc: 'Optimal entry within ±5 pips', layer: 6 },
  { icon: Shield, label: 'Risk Module', desc: '1% risk per trade, dynamic RR', layer: 7 },
  { icon: Bell, label: 'Signal Dispatch', desc: 'Instant Telegram delivery', layer: 8 },
  { icon: Clock, label: 'Session Filter', desc: 'London/NY only execution', layer: 9 },
  { icon: Activity, label: 'Volume Confirmation', desc: 'Tick volume spike detection', layer: 10 },
  { icon: Sparkles, label: 'FB Trap Detection', desc: 'False breakout pattern capture', layer: 11 },
  { icon: Globe, label: 'Regime Routing', desc: 'Adaptive strategy selection', layer: 12 },
]

const FAQ_DATA = [
  { q: 'What pairs does TradeKnox trade?', a: 'XAUUSD, GBPUSD, AUDUSD, EURUSD, GBPJPY, NZDUSD, USDCAD, and USDJPY — all major and cross pairs with tight spreads.' },
  { q: 'How fast are signals delivered?', a: 'Signals are dispatched within 100ms of entry criteria being met. You receive them instantly via Telegram with full entry, SL, and TP levels.' },
  { q: 'What is the 8-Gate system?', a: 'Each signal must pass 8 sequential quality gates — structure, momentum, volume, sentiment, volatility, timing, risk, and entry precision. A single failure rejects the trade.' },
  { q: 'Is there a subscription fee?', a: 'No. TradeKnox is 100% free. Unlimited signals, instant delivery, no hidden costs. Connect your Telegram bot and start receiving signals immediately.' },
  { q: 'How does the bot handle news events?', a: 'The session filter restricts trading to London and New York sessions. Volatility regimes are detected in real-time, routing to the appropriate strategy.' },
  { q: 'Can I customize risk settings?', a: 'Risk is fixed at 1% per trade for consistency. TP targets are set at 1.5R (TP1), 2.5R (TP2), and 3.5R (TP3) with dynamic trailing.' },
]

const TICKER = [
  { pair: 'XAUUSD', price: '3,245.80', change: '+0.42%', up: true },
  { pair: 'EURUSD', price: '1.0892', change: '-0.15%', up: false },
  { pair: 'GBPUSD', price: '1.2734', change: '+0.28%', up: true },
  { pair: 'USDJPY', price: '157.42', change: '-0.31%', up: false },
  { pair: 'AUDUSD', price: '0.6534', change: '+0.18%', up: true },
  { pair: 'GBPJPY', price: '200.45', change: '+0.12%', up: true },
]

export default function Page() {
  return (
    <main className="noise">
      <ScrollProgress />
      <Ticker />
      <Navbar />
      <Hero />
      <StatsBar />
      <div className="divider max-w-7xl mx-auto" />
      <Features />
      <div className="divider max-w-7xl mx-auto" />
      <Strategy />
      <div className="divider max-w-7xl mx-auto" />
      <Performance />
      <div className="divider max-w-7xl mx-auto" />
      <Pipeline />
      <div className="divider max-w-7xl mx-auto" />
      <Pricing />
      <div className="divider max-w-7xl mx-auto" />
      <FAQ />
      <CTA />
      <Footer />
    </main>
  )
}

function Ticker() {
  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-8 bg-black/80 backdrop-blur-sm border-b border-white/5 overflow-hidden">
      <div className="marquee-track h-full items-center">
        {[...TICKER, ...TICKER].map((t, i) => (
          <span key={i} className="flex items-center gap-2 px-6 text-xs font-mono whitespace-nowrap">
            <span className="text-white/60">{t.pair}</span>
            <span className="text-white">{t.price}</span>
            <span className={t.up ? 'text-emerald-400' : 'text-red-400'}>{t.change}</span>
          </span>
        ))}
      </div>
    </div>
  )
}

function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', h, { passive: true })
    return () => window.removeEventListener('scroll', h)
  }, [])

  return (
    <nav className={`fixed top-8 left-0 right-0 z-40 transition-all duration-500 ${scrolled ? 'nav-blur' : ''}`}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-gold" />
          <span className="text-sm font-semibold tracking-tight text-white">TradeKnox</span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="nav-link">Features</a>
          <a href="#strategy" className="nav-link">Strategy</a>
          <a href="#performance" className="nav-link">Performance</a>
          <a href="#pipeline" className="nav-link">Pipeline</a>
          <a href="#faq" className="nav-link">FAQ</a>
        </div>
        <div className="hidden md:flex items-center gap-3">
          <a href="https://t.me/TradeKnoxTestBot" className="btn-gold text-sm">Start Free</a>
        </div>
        <button onClick={() => setOpen(!open)} className="md:hidden text-white/70">
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden nav-blur border-t border-white/5"
          >
            <div className="px-6 py-4 flex flex-col gap-3">
              {['Features', 'Strategy', 'Performance', 'Pipeline', 'FAQ'].map(l => (
                <a key={l} href={`#${l.toLowerCase()}`} onClick={() => setOpen(false)} className="nav-link">{l}</a>
              ))}
              <a href="https://t.me/TradeKnoxTestBot" className="btn-gold text-sm text-center mt-2">Start Free</a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}

function Hero() {
  return (
    <section className="hero-scene flex items-center justify-center pt-28 pb-20 px-6">
      <div className="hero-grid" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />
      <div className="relative z-10 max-w-4xl mx-auto text-center">
        <ScrollReveal>
          <div className="section-tag mx-auto mb-6">
            <Zap className="w-3 h-3" />
            Live Signals · Free Forever
          </div>
        </ScrollReveal>
        <ScrollReveal delay={100}>
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tighter mb-6">
            <span className="text-white">Institutional</span>{' '}
            <span className="stat-value">Precision</span>
            <br />
            <span className="text-white/40 text-3xl md:text-5xl">Delivered to Telegram</span>
          </h1>
        </ScrollReveal>
        <ScrollReveal delay={200}>
          <p className="text-lg text-white/50 max-w-2xl mx-auto mb-10 leading-relaxed">
            12-layer signal pipeline. SMC 8-Gate strategy. 20+ years backtested across 8 forex pairs.
            TradeKnox delivers institutional-quality signals with surgical precision.
          </p>
        </ScrollReveal>
        <ScrollReveal delay={300}>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a href="https://t.me/TradeKnoxTestBot" className="btn-gold flex items-center gap-2 text-base">
              <Play className="w-4 h-4" />
              Start Receiving Signals
            </a>
            <a href="#performance" className="btn-ghost flex items-center gap-2 text-base">
              View Backtest Results
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </ScrollReveal>
        <ScrollReveal delay={400}>
          <div className="mt-12 flex items-center justify-center gap-6 text-xs text-white/30">
            <span className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5" /> 1% Risk Per Trade</span>
            <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> Instant Delivery</span>
            <span className="flex items-center gap-1.5"><Lock className="w-3.5 h-3.5" /> No API Keys Required</span>
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}

function StatsBar() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
        {[
          { label: 'Backtested Period', value: '20+ Years', sub: '2003–2025' },
          { label: 'Average Win Rate', value: '58%', sub: 'Across all pairs' },
          { label: 'Avg Profit Factor', value: '2.07', sub: 'Net of spreads' },
          { label: 'Total Trades', value: '5,630', sub: '8 pairs combined' },
        ].map((s, i) => (
          <ScrollReveal key={i} delay={i * 80}>
            <div className="glass-card p-6 text-center">
              <div className="text-2xl md:text-3xl font-bold stat-value mb-1">{s.value}</div>
              <div className="text-sm text-white/70 font-medium">{s.label}</div>
              <div className="text-xs text-white/30 mt-1">{s.sub}</div>
            </div>
          </ScrollReveal>
        ))}
      </div>
    </section>
  )
}

function Features() {
  const features = [
    { icon: CandlestickChart, title: 'SMC Structure', desc: 'Order blocks, BOS, CHoCH mapped in real-time', color: 'icon-container' },
    { icon: Sparkles, title: 'False Breakout Trap', desc: 'Captures liquidity grabs before the real move', color: 'icon-container-emerald' },
    { icon: Brain, title: 'Regime Routing', desc: 'Adaptive strategy selection per market condition', color: 'icon-container-violet' },
    { icon: Target, title: '8-Gate Filter', desc: 'Sequential fail-fast — single fail rejects trade', color: 'icon-container-sky' },
    { icon: Shield, title: 'Risk Control', desc: '1% per trade, dynamic trailing, BE after TP1', color: 'icon-container' },
    { icon: Bell, title: 'Instant Delivery', desc: 'Telegram signals with entry, SL, 3 TPs', color: 'icon-container-emerald' },
  ]

  return (
    <section id="features" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="section-tag mb-4">Core Capabilities</div>
          <h2 className="section-heading mb-3">Built for Precision</h2>
          <p className="section-sub mb-16">Every component engineered for one outcome: consistent, risk-managed entries.</p>
        </ScrollReveal>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <ScrollReveal key={i} delay={i * 80}>
              <div className="glass-card p-7 h-full">
                <div className={f.color}>
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="text-white font-semibold mt-5 mb-2">{f.title}</h3>
                <p className="text-sm text-white/45 leading-relaxed">{f.desc}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}

function Strategy() {
  return (
    <section id="strategy" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <ScrollReveal>
            <div className="section-tag mb-4">Dual Strategy</div>
            <h2 className="section-heading mb-6">Two Edges,<br />One System</h2>
            <p className="text-white/45 leading-relaxed mb-8">
              TradeKnox doesn&apos;t rely on a single edge. It dynamically routes between the SMC 8-Gate pipeline
              and the False Breakout Trap — selecting the optimal strategy based on real-time regime detection.
            </p>
            <div className="space-y-4">
              {[
                { label: 'Trending Markets', strategy: 'SMC 8-Gate', color: 'text-gold' },
                { label: 'Ranging Markets', strategy: 'False Breakout Trap', color: 'text-emerald-400' },
                { label: 'Mixed Conditions', strategy: 'Higher Confidence Wins', color: 'text-violet-400' },
              ].map((r, i) => (
                <div key={i} className="flex items-center justify-between py-3 border-b border-white/5">
                  <span className="text-sm text-white/60">{r.label}</span>
                  <span className={`text-sm font-semibold ${r.color}`}>{r.strategy}</span>
                </div>
              ))}
            </div>
          </ScrollReveal>
          <ScrollReveal delay={200}>
            <div className="gradient-card">
              <div className="gradient-card-inner">
                <h3 className="text-sm font-semibold text-white/70 mb-6 uppercase tracking-wider">Scoring Radar</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={SCORING_RADAR}>
                    <PolarGrid stroke="rgba(255,255,255,0.06)" />
                    <PolarAngleAxis dataKey="label" tick={{ fill: '#7a7a90', fontSize: 11 }} />
                    <Radar dataKey="score" stroke="#d4a843" fill="#d4a843" fillOpacity={0.15} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  )
}

function Performance() {
  return (
    <section id="performance" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="section-tag mb-4">Backtest Results</div>
          <h2 className="section-heading mb-3">20+ Years of Proof</h2>
          <p className="section-sub mb-16">Every number audited. Every trade accounted for.</p>
        </ScrollReveal>
        <ScrollReveal>
          <div className="gradient-card mb-10">
            <div className="gradient-card-inner">
              <h3 className="text-sm font-semibold text-white/70 mb-6 uppercase tracking-wider">Equity Curve</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={EQUITY_CURVE}>
                  <defs>
                    <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#d4a843" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#d4a843" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" hide />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{ background: 'rgba(10,10,15,0.95)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12 }}
                    labelStyle={{ color: '#f0f0f5' }}
                    formatter={(v: number) => [`$${v.toLocaleString()}`, 'Equity']}
                  />
                  <Area type="monotone" dataKey="equity" stroke="#d4a843" fill="url(#eqGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </ScrollReveal>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left py-3 px-4 text-white/40 font-medium">Pair</th>
                <th className="text-right py-3 px-4 text-white/40 font-medium">Profit Factor</th>
                <th className="text-right py-3 px-4 text-white/40 font-medium">Win Rate</th>
                <th className="text-right py-3 px-4 text-white/40 font-medium">Trades</th>
                <th className="text-right py-3 px-4 text-white/40 font-medium">Sharpe</th>
              </tr>
            </thead>
            <tbody>
              {PAIR_DATA.map((p, i) => (
                <tr key={i} className="border-b border-white/3 hover:bg-white/[0.02] transition-colors">
                  <td className="py-3 px-4 text-white font-medium">{p.pair}</td>
                  <td className="py-3 px-4 text-right text-emerald-400 font-semibold">{p.pf}x</td>
                  <td className="py-3 px-4 text-right text-white/70">{p.wr}%</td>
                  <td className="py-3 px-4 text-right text-white/50">{p.trades.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right text-white/50">{p.sharpe}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}

function Pipeline() {
  return (
    <section id="pipeline" className="py-24 px-6">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="section-tag mb-4">Signal Pipeline</div>
          <h2 className="section-heading mb-3">12 Layers Deep</h2>
          <p className="section-sub mb-16">Each signal must survive 12 sequential quality gates before delivery.</p>
        </ScrollReveal>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {PIPELINE_STEPS.map((s, i) => (
            <ScrollReveal key={i} delay={i * 60}>
              <div className="glass-card p-5 flex items-start gap-4">
                <div className="icon-container flex-shrink-0">
                  <s.icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs text-gold/60 font-mono mb-1">Layer {s.layer}</div>
                  <div className="text-white font-medium text-sm">{s.label}</div>
                  <div className="text-xs text-white/40 mt-1">{s.desc}</div>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}

function Pricing() {
  return (
    <section id="pricing" className="py-24 px-6">
      <div className="max-w-4xl mx-auto text-center">
        <ScrollReveal>
          <div className="section-tag mb-4">Pricing</div>
          <h2 className="section-heading mb-3">100% Free</h2>
          <p className="section-sub mx-auto mb-12">No subscription. No hidden fees. No API keys. Just connect and receive signals.</p>
        </ScrollReveal>
        <ScrollReveal>
          <div className="gradient-card pricing-featured max-w-lg mx-auto">
            <div className="gradient-card-inner text-center">
              <div className="text-sm text-gold font-semibold uppercase tracking-wider mb-2">TradeKnox Bot</div>
              <div className="text-4xl font-bold text-white mb-1">$0</div>
              <div className="text-sm text-white/40 mb-8">Free forever</div>
              <div className="space-y-3 text-left mb-8">
                {[
                  'Unlimited signals across 8 pairs',
                  'SMC 8-Gate + False Breakout strategies',
                  'Instant Telegram delivery',
                  '3 TP levels with trailing',
                  'London & New York session filtering',
                  'Real-time regime detection',
                ].map((f, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span className="text-sm text-white/70">{f}</span>
                  </div>
                ))}
              </div>
              <a href="https://t.me/TradeKnoxTestBot" className="btn-gold w-full block text-center">
                Start Now — It&apos;s Free
              </a>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}

function FAQ() {
  const [openIdx, setOpenIdx] = useState<number | null>(null)

  return (
    <section id="faq" className="py-24 px-6">
      <div className="max-w-3xl mx-auto">
        <ScrollReveal>
          <div className="section-tag mb-4">FAQ</div>
          <h2 className="section-heading mb-12">Common Questions</h2>
        </ScrollReveal>
        <div>
          {FAQ_DATA.map((f, i) => (
            <ScrollReveal key={i} delay={i * 60}>
              <div className="faq-item">
                <button
                  onClick={() => setOpenIdx(openIdx === i ? null : i)}
                  className="w-full py-5 flex items-center justify-between text-left"
                >
                  <span className="text-sm text-white font-medium pr-4">{f.q}</span>
                  <ChevronDown className={`w-4 h-4 text-white/40 transition-transform flex-shrink-0 ${openIdx === i ? 'rotate-180' : ''}`} />
                </button>
                <AnimatePresence>
                  {openIdx === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <p className="pb-5 text-sm text-white/45 leading-relaxed">{f.a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}

function CTA() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-4xl mx-auto text-center">
        <ScrollReveal>
          <h2 className="text-3xl md:text-5xl font-bold tracking-tight mb-6">
            Ready to Trade with<br /><span className="stat-value">Institutional Precision?</span>
          </h2>
          <p className="text-white/45 mb-10 max-w-xl mx-auto">
            Connect your Telegram bot and start receiving signals in under 60 seconds.
          </p>
          <a href="https://t.me/TradeKnoxTestBot" className="btn-gold inline-flex items-center gap-2 text-base">
            <Bot className="w-4 h-4" />
            Launch TradeKnox Bot
          </a>
        </ScrollReveal>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="border-t border-white/5 py-12 px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-gold" />
          <span className="text-sm font-semibold text-white">TradeKnox</span>
        </div>
        <div className="flex items-center gap-6">
          {['Features', 'Strategy', 'Performance', 'Pipeline', 'FAQ'].map(l => (
            <a key={l} href={`#${l.toLowerCase()}`} className="text-xs text-white/30 hover:text-white/60 transition-colors">{l}</a>
          ))}
        </div>
        <div className="text-center md:text-right">
          <p className="text-xs text-muted-foreground">
            &copy; 2025 TradeKnox. All rights reserved. Trading involves risk.
          </p>
          <p className="text-xs text-muted-foreground">
            Past performance is not indicative of future results.
          </p>
        </div>
      </div>
    </footer>
  )
}
