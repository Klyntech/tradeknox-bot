import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Menu, X, TrendingUp, Shield, Target, Zap, BarChart3, Clock, ChevronRight, ArrowRight } from 'lucide-react'

const SIGNALS = [
  { pair: 'XAUUSD', dir: 'BUY', entry: '3,245.50', sl: '3,232.20', tp: '3,268.40', conf: 78, session: 'London', reason: 'OB + FVG confluence' },
  { pair: 'GBPJPY', dir: 'SELL', entry: '192.850', sl: '193.350', tp: '191.850', conf: 72, session: 'Overlap', reason: 'Bearish BOS + RSI div' },
]

const FEATURES = [
  { icon: TrendingUp, title: 'Structure-First', desc: 'Market structure, BOS/CHoCH, and trend detection before any indicator.' },
  { icon: Shield, title: 'Order Blocks', desc: 'Institutional supply and demand zones with strength scoring.' },
  { icon: Target, title: 'Weighted Scoring', desc: '0–20 point system across 6 categories. Below threshold = no trade.' },
  { icon: BarChart3, title: 'Risk Engine', desc: 'ATR-based SL/TP, position sizing, and R:R validation.' },
]

const PLANS = [
  { name: 'Free', price: '$0', period: 'forever', features: ['3 signals/day', '15 min delay', 'Basic analysis', 'Community'], cta: 'Get Started', highlight: false },
  { name: 'Pro', price: '$29', period: '/mo', features: ['Unlimited signals', 'Instant delivery', 'Full analysis', 'Priority support'], cta: 'Subscribe', highlight: true },
  { name: 'VIP', price: '$49', period: '/mo', features: ['Everything in Pro', 'Risk alerts', 'SMC Blueprint course', '1-on-1 coaching'], cta: 'Subscribe', highlight: false },
]

function Nav() {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', h)
    return () => window.removeEventListener('scroll', h)
  }, [])

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-surface/80 backdrop-blur-xl border-b border-white/5' : 'bg-transparent'}`}>
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <a href="#" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gold rounded-lg flex items-center justify-center text-black font-bold text-sm">TK</div>
          <span className="font-bold text-white tracking-tight">TRADEKNOX</span>
        </a>

        <div className="hidden md:flex items-center gap-8 text-sm text-neutral-400">
          <a href="#features" className="hover:text-gold transition-colors">Features</a>
          <a href="#signals" className="hover:text-gold transition-colors">Signals</a>
          <a href="#stats" className="hover:text-gold transition-colors">Performance</a>
          <a href="#plans" className="hover:text-gold transition-colors">Plans</a>
          <a href="https://t.me/TradeKnoxBot" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-gold text-black font-semibold rounded-lg hover:bg-gold-light transition-colors">
            Open Bot
          </a>
        </div>

        <button className="md:hidden text-white" onClick={() => setOpen(!open)}>
          {open ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-surface border-b border-white/5 overflow-hidden"
          >
            <div className="px-6 py-4 flex flex-col gap-4">
              <a href="#features" onClick={() => setOpen(false)} className="text-neutral-400 hover:text-gold transition-colors">Features</a>
              <a href="#signals" onClick={() => setOpen(false)} className="text-neutral-400 hover:text-gold transition-colors">Signals</a>
              <a href="#stats" onClick={() => setOpen(false)} className="text-neutral-400 hover:text-gold transition-colors">Performance</a>
              <a href="#plans" onClick={() => setOpen(false)} className="text-neutral-400 hover:text-gold transition-colors">Plans</a>
              <a href="https://t.me/TradeKnoxBot" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-gold text-black font-semibold rounded-lg text-center">Open Bot</a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}

function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(212,168,67,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(212,168,67,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />

      {/* Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gold/5 rounded-full blur-[120px]" />

      <div className="relative z-10 text-center px-6 max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-gold/20 bg-gold/5 text-gold text-xs font-medium tracking-wider uppercase mb-8"
        >
          <span className="w-1.5 h-1.5 bg-gold rounded-full animate-pulse" />
          Backtested Strategies
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-5xl md:text-7xl lg:text-8xl font-black text-white tracking-tighter leading-[0.9] mb-6"
        >
          TradeKnox
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-xl md:text-2xl text-neutral-400 font-light max-w-2xl mx-auto mb-4"
        >
          Structure-first trading signals
        </motion.p>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-sm text-neutral-500 max-w-xl mx-auto mb-10"
        >
          SMC analysis — order blocks, FVGs, Fibonacci, liquidity zones — scored against a weighted confidence system. Only signals above threshold fire.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="flex flex-col sm:flex-row gap-4 justify-center"
        >
          <a href="#plans" className="px-8 py-3 bg-gold text-black font-semibold rounded-lg hover:bg-gold-light transition-colors flex items-center justify-center gap-2">
            Get Started <ArrowRight size={16} />
          </a>
          <a href="#signals" className="px-8 py-3 border border-white/10 text-white font-medium rounded-lg hover:border-gold/30 hover:text-gold transition-colors">
            View Signals
          </a>
        </motion.div>
      </div>
    </section>
  )
}

function Features() {
  return (
    <section id="features" className="py-24 border-t border-white/5">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <p className="text-gold text-xs font-medium tracking-widest uppercase mb-3">Methodology</p>
          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight">How It Works</h2>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="p-6 rounded-xl border border-white/5 bg-surface-raised hover:border-gold/20 transition-colors group"
            >
              <div className="w-10 h-10 rounded-lg bg-gold/10 flex items-center justify-center mb-4 group-hover:bg-gold/20 transition-colors">
                <f.icon size={20} className="text-gold" />
              </div>
              <h3 className="text-white font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-neutral-500 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

function SignalFeed() {
  return (
    <section id="signals" className="py-24 border-t border-white/5">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <p className="text-gold text-xs font-medium tracking-widest uppercase mb-3">Live Feed</p>
          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight">Recent Signals</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {SIGNALS.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="p-5 rounded-xl border border-white/5 bg-surface-raised hover:border-gold/20 transition-colors"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="text-white font-bold text-lg">{s.pair}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${s.dir === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                    {s.dir}
                  </span>
                </div>
                <span className="text-gold font-mono text-sm font-bold">{s.conf}%</span>
              </div>

              <div className="grid grid-cols-3 gap-3 text-xs">
                <div>
                  <span className="text-neutral-600 block mb-1">Entry</span>
                  <span className="text-white font-mono">{s.entry}</span>
                </div>
                <div>
                  <span className="text-neutral-600 block mb-1">SL</span>
                  <span className="text-red-400 font-mono">{s.sl}</span>
                </div>
                <div>
                  <span className="text-neutral-600 block mb-1">TP</span>
                  <span className="text-emerald-400 font-mono">{s.tp}</span>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-neutral-500">
                <span className="flex items-center gap-1"><Clock size={12} /> {s.session}</span>
                <span>{s.reason}</span>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="text-center mt-8">
          <a href="https://t.me/TradeKnoxSignals" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 text-sm text-gold hover:text-gold-light transition-colors">
            View all signals on Telegram <ChevronRight size={14} />
          </a>
        </div>
      </div>
    </section>
  )
}

function Stats() {
  const stats = [
    { value: '53%', label: 'Win Rate', sub: 'Combined 6-month backtest' },
    { value: '1.45', label: 'Avg R:R', sub: 'Risk to reward' },
    { value: '116', label: 'Signals', sub: 'XAUUSD + GBPJPY' },
    { value: '11/20', label: 'Min Score', sub: 'Threshold enforced' },
  ]

  return (
    <section id="stats" className="py-24 border-t border-white/5 bg-surface-raised">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <p className="text-gold text-xs font-medium tracking-widest uppercase mb-3">Performance</p>
          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight">Results</h2>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="text-center p-6 rounded-xl border border-white/5 bg-surface"
            >
              <div className="text-4xl md:text-5xl font-black text-gold mb-2 font-mono">{s.value}</div>
              <div className="text-white font-semibold mb-1">{s.label}</div>
              <div className="text-xs text-neutral-500">{s.sub}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Plans() {
  return (
    <section id="plans" className="py-24 border-t border-white/5">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <p className="text-gold text-xs font-medium tracking-widest uppercase mb-3">Pricing</p>
          <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight">Choose Your Edge</h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {PLANS.map((p, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className={`relative p-8 rounded-xl border ${p.highlight ? 'border-gold/30 bg-gold/5' : 'border-white/5 bg-surface-raised'}`}
            >
              {p.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gold text-black text-xs font-bold rounded-full">
                  POPULAR
                </div>
              )}

              <h3 className={`text-xl font-bold mb-2 ${p.highlight ? 'text-gold' : 'text-white'}`}>{p.name}</h3>
              <div className="flex items-baseline gap-1 mb-6">
                <span className="text-4xl font-black text-white">{p.price}</span>
                <span className="text-sm text-neutral-500">{p.period}</span>
              </div>

              <ul className="space-y-3 mb-8">
                {p.features.map((f, fi) => (
                  <li key={fi} className="flex items-center gap-2 text-sm text-neutral-400">
                    <Zap size={14} className={p.highlight ? 'text-gold' : 'text-neutral-600'} />
                    {f}
                  </li>
                ))}
              </ul>

              <button className={`w-full py-3 rounded-lg text-sm font-semibold transition-colors ${
                p.highlight
                  ? 'bg-gold text-black hover:bg-gold-light'
                  : 'border border-white/10 text-white hover:border-gold/30 hover:text-gold'
              }`}>
                {p.cta}
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="border-t border-white/5 py-12">
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-gold rounded-lg flex items-center justify-center text-black font-bold text-xs">TK</div>
          <span className="font-bold text-white">TradeKnox</span>
        </div>

        <div className="flex gap-6 text-sm text-neutral-500">
          <a href="https://github.com/Klyntech/tradeknox-bot" target="_blank" rel="noopener noreferrer" className="hover:text-gold transition-colors">GitHub</a>
          <a href="https://t.me/TradeKnoxBot" target="_blank" rel="noopener noreferrer" className="hover:text-gold transition-colors">Telegram</a>
        </div>

        <p className="text-xs text-neutral-600">© 2026 TradeKnox. Not financial advice.</p>
      </div>
    </footer>
  )
}

function App() {
  return (
    <div className="min-h-screen bg-surface text-neutral-300">
      <Nav />
      <Hero />
      <Features />
      <SignalFeed />
      <Stats />
      <Plans />
      <Footer />
    </div>
  )
}

export default App
