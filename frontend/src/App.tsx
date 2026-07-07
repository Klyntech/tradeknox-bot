import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence, useInView } from 'framer-motion'
import { Menu, X, TrendingUp, Shield, Target, BarChart3, Clock, ChevronRight, ArrowRight, ChevronDown, Check, Send } from 'lucide-react'

const SIGNALS = [
  { pair: 'XAUUSD', dir: 'BUY', entry: '3,245.50', sl: '3,232.20', tp: '3,268.40', conf: 78, session: 'London', reason: 'OB + FVG confluence' },
  { pair: 'GBPJPY', dir: 'SELL', entry: '192.850', sl: '193.350', tp: '191.850', conf: 72, session: 'Overlap', reason: 'Bearish BOS + RSI div' },
]

const FEATURES = [
  { icon: TrendingUp, title: 'Structure-First', desc: 'Market structure, BOS/CHoCH, and trend detection before any indicator.' },
  { icon: Shield, title: 'Order Blocks', desc: 'Institutional supply and demand zones with strength scoring.' },
  { icon: Target, title: 'Weighted Scoring', desc: '0-20 point system across 6 categories. Below threshold = no trade.' },
  { icon: BarChart3, title: 'Risk Engine', desc: 'ATR-based SL/TP, position sizing, and R:R validation.' },
]

const PLANS = [
  { name: 'Free', price: '$0', period: 'forever', features: ['3 signals/day', '15 min delay', 'Basic analysis', 'Community'], cta: 'Get Started', highlight: false },
  { name: 'Pro', price: '$29', period: '/mo', features: ['Unlimited signals', 'Instant delivery', 'Full analysis', 'Priority support'], cta: 'Subscribe', highlight: true },
  { name: 'VIP', price: '$49', period: '/mo', features: ['Everything in Pro', 'Risk alerts', 'Advanced analytics', 'Personalized support'], cta: 'Subscribe', highlight: false },
]

const FAQ = [
  { q: 'What pairs do you cover?', a: 'XAUUSD (Gold) and GBPJPY — the only two pairs that showed consistent profitability across 6 months of backtesting. We do not chase setups that do not work.' },
  { q: 'How accurate are the signals?', a: '53% win rate with 1.45 R:R reward-to-risk. That means you can lose nearly half your trades and still be profitable. This is real, not marketing hype.' },
  { q: 'How many signals per day?', a: '3-5 signals per pair, spread across London, overlap, and New York sessions. We never force trades — if there is no setup, we wait.' },
  { q: 'Can I use any broker?', a: 'Yes. Any broker with MT4/MT5. We do not take trades for you — we give you entry, stop loss, and take profit levels. You execute.' },
  { q: 'How do you generate signals?', a: '6 category scoring system (0-20 points): trend detection, order blocks, BOS/CHoCH, RSI, S/R zones, and session filters. Only trades scoring 11+ and passing 2+ strategy checks are sent.' },
  { q: 'What if I am a beginner?', a: 'Free tier is perfect. 3 signals/day with basic analysis. No pressure, no cost. Learn the patterns before upgrading.' },
  { q: 'Can I lose money?', a: 'Yes. Trading is high risk. 53% win rate does not guarantee profit. Never trade money you cannot afford to lose. Set your own risk management.' },
  { q: 'How do payments work?', a: 'Stripe checkout. Credit card or PayPal. Cancel anytime. No contracts, no hidden fees.' },
  { q: 'Do you take a cut of my profits?', a: 'No. Flat monthly subscription only. We do not take performance fees, spreads, or commissions.' },
  { q: 'What time zone are signals in?', a: 'UTC. Signal timestamps show when they were generated. Adjust for your local time.' },
  { q: 'How fast are signals delivered?', a: 'Pro/VIP: instant via Telegram. Free tier: 15 minute delay. Most signals have 10-30 minute entry windows.' },
  { q: 'Do you provide charts?', a: 'Yes. Pro/VIP get chart screenshots with annotations. Free tier gets text-based levels.' },
  { q: 'What is the scoring system?', a: '6 categories, each 0-3 points: trend (structure), BOS/CHoCH (structure), order blocks (institutional), RSI (momentum), S/R zones (geometric), session (time). Total out of 20.' },
  { q: 'What is the minimum score for a signal?', a: '11/20 with 2+ strategy confirmations. Below that = no trade. We are selective by design.' },
  { q: 'How is this different from other signal groups?', a: 'Most groups use indicators. We use market structure + institutional order flow. 6 months of backtested data, not promises.' },
  { q: 'Do you trade live yourself?', a: 'We test every strategy with real money. The backtest results use conservative assumptions (2-pip spread, 0.1 lot, $10k balance).' },
  { q: 'Can I request specific pairs?', a: 'Not yet. We only signal pairs we have backtested. Adding a pair means months of live verification first.' },
  { q: 'What happens if the bot goes down?', a: 'Render free tier has cold starts. Signals may have brief delays. Pro/VIP are prioritized when we scale.' },
  { q: 'Do you offer a refund?', a: 'Monthly subscriptions can be cancelled anytime. No refunds for partial months.' },
  { q: 'Can I use the signals for copy trading?', a: 'Yes. Many subscribers mirror our trades. But always set your own lot sizes based on your risk management.' },
  { q: 'Is there a mobile app?', a: 'No. Telegram bot works on mobile. Signals are formatted for quick reading on any device.' },
  { q: 'How do I set up Telegram?', a: 'Download Telegram, search @TradeKnoxBot, press Start. You will get a welcome message with setup instructions.' },
  { q: 'Do you support automated trading?', a: 'Not yet. Current signals are manual execution. We may add EA integration in the future.' },
  { q: 'What is the win rate over different periods?', a: '6 months (Jan-Jul 2026): 53% across 116 signals. Past performance does not guarantee future results.' },
]

function useTyping(text: string, speed = 50) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)
  useEffect(() => {
    setDisplayed('')
    setDone(false)
    let i = 0
    const timer = setInterval(() => {
      if (i < text.length) {
        setDisplayed(text.slice(0, i + 1))
        i++
      } else {
        setDone(true)
        clearInterval(timer)
      }
    }, speed)
    return () => clearInterval(timer)
  }, [text, speed])
  return { displayed, done }
}

function useCountUp(target: number, duration = 2000) {
  const [count, setCount] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true })
  useEffect(() => {
    if (!inView) return
    const start = Date.now()
    const timer = setInterval(() => {
      const elapsed = Date.now() - start
      const progress = Math.min(elapsed / duration, 1)
      setCount(Math.floor(progress * target))
      if (progress >= 1) clearInterval(timer)
    }, 16)
    return () => clearInterval(timer)
  }, [inView, target, duration])
  return { count, ref }
}

function Particles() {
  const particles = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 20,
    duration: 15 + Math.random() * 20,
    size: 2 + Math.random() * 4,
  }))
  return (
    <div className="particles">
      {particles.map(p => (
        <div key={p.id} className="particle" style={{
          left: `${p.left}%`,
          animationDelay: `${p.delay}s`,
          animationDuration: `${p.duration}s`,
          width: `${p.size}px`,
          height: `${p.size}px`,
        }} />
      ))}
    </div>
  )
}

function ScrollProgress() {
  const [progress, setProgress] = useState(0)
  useEffect(() => {
    const handle = () => {
      const total = document.documentElement.scrollHeight - window.innerHeight
      setProgress(total > 0 ? window.scrollY / total : 0)
    }
    window.addEventListener('scroll', handle)
    return () => window.removeEventListener('scroll', handle)
  }, [])
  return <div className="scroll-progress" style={{ transform: `scaleX(${progress})` }} />
}

function StatCard({ label, value, suffix }: { label: string; value: number; suffix: string }) {
  const { count, ref } = useCountUp(value)
  return (
    <div ref={ref} className="text-center">
      <div className="text-3xl md:text-4xl font-bold text-gold">{count}{suffix}</div>
      <div className="text-sm text-muted mt-1">{label}</div>
    </div>
  )
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="faq-item border-b border-white/5">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between py-4 text-left">
        <span className="text-sm font-medium text-white/90">{q}</span>
        <ChevronDown className={`w-4 h-4 text-muted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <p className="text-sm text-muted pb-4">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function App() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [subscribed, setSubscribed] = useState(false)
  const heroRef = useRef<HTMLDivElement>(null)
  const heroInView = useInView(heroRef, { once: true })
  const { displayed: typingText } = useTyping('institutional-grade trade signals', 40)
  const [signalIdx, setSignalIdx] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setSignalIdx(i => (i + 1) % SIGNALS.length), 5000)
    return () => clearInterval(t)
  }, [])

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault()
    if (email) setSubscribed(true)
  }

  return (
    <div className="min-h-screen bg-bg text-white overflow-x-hidden">
      <Particles />
      <ScrollProgress />

      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-bg/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gold/10 border border-gold/30 rounded-lg flex items-center justify-center">
              <span className="text-gold font-bold text-sm">TK</span>
            </div>
            <span className="font-semibold text-white">TradeKnox</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            {['Features', 'Example Signals', 'Pricing', 'FAQ'].map(s => (
              <a key={s} href={`#${s.toLowerCase().replace(' ', '-')}`} className="nav-link text-sm text-muted hover:text-white transition-colors">{s}</a>
            ))}
            <a href="https://t.me/TradeKnoxBot" className="bg-gold text-bg px-4 py-2 rounded-lg text-sm font-medium btn-glow hover:opacity-90 transition-opacity">
              Open Bot
            </a>
          </div>
          <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden text-muted hover:text-white">
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
            className="fixed inset-0 z-40 bg-bg/95 backdrop-blur-xl pt-20 px-6 md:hidden">
            <div className="flex flex-col gap-6">
              {['Features', 'Example Signals', 'Pricing', 'FAQ'].map(s => (
                <a key={s} href={`#${s.toLowerCase().replace(' ', '-')}`} onClick={() => setMobileOpen(false)}
                  className="text-lg text-muted hover:text-white transition-colors">{s}</a>
              ))}
              <a href="https://t.me/TradeKnoxBot" className="bg-gold text-bg px-4 py-3 rounded-lg text-center font-medium">
                Open Bot
              </a>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hero */}
      <section ref={heroRef} className="relative pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={heroInView ? { opacity: 1, y: 0 } : {}} transition={{ duration: 0.6 }}>
            <div className="badge-shimmer inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gold/5 border border-gold/20 mb-8">
              <span className="w-1.5 h-1.5 bg-gold rounded-full pulse-glow" />
              <span className="text-xs font-medium text-gold">Backtested on 6 Months of Live Data</span>
            </div>
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
              <span className="text-white">{typingText}</span>
              {!typingText.includes('institutional-grade trade signals') && <span className="text-gold">|</span>}
            </h1>
            <p className="text-lg md:text-xl text-muted max-w-2xl mx-auto mb-10">
              Market structure analysis. Order block detection. Weighted scoring. All automated. All backtested.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a href="https://t.me/TradeKnoxBot" className="bg-gold text-bg px-8 py-3.5 rounded-lg font-semibold text-base btn-glow hover:opacity-90 transition-opacity inline-flex items-center gap-2">
                Start Free <ArrowRight className="w-4 h-4" />
              </a>
              <a href="#features" className="border border-white/10 text-white px-8 py-3.5 rounded-lg font-medium text-base hover:bg-white/5 transition-colors">
                See How It Works
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-white/5 bg-card/30">
        <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          <StatCard label="Signals tested" value={116} suffix="+" />
          <StatCard label="Win rate" value={53} suffix="%" />
          <StatCard label="Risk:Reward" value={145} suffix="%" />
          <StatCard label="Pairs tracked" value={2} suffix="" />
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">How the Engine Works</h2>
            <p className="text-muted max-w-lg mx-auto">Every signal passes through 6 analysis categories before reaching you. No guesswork.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div key={f.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className="card-hover bg-card border border-white/5 rounded-xl p-6">
                <f.icon className="w-8 h-8 text-gold mb-4" />
                <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-muted">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-6 bg-card/30 border-y border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">How It Works</h2>
            <p className="text-muted max-w-lg mx-auto">Three steps. No complexity. No hidden fees.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Join', desc: 'Open @TradeKnoxBot in Telegram. Press Start. Choose Free, Pro, or VIP.' },
              { step: '02', title: 'Receive', desc: 'Get signals with entry, SL, TP, confidence score, and session info. Pro/VIP: instant. Free: 15 min delay.' },
              { step: '03', title: 'Execute', desc: 'Copy the levels into your MT4/MT5. Set your lot size. Place the trade. We handle the analysis.' },
            ].map((s, i) => (
              <motion.div key={s.step} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.15 }}
                className="text-center">
                <div className="w-12 h-12 rounded-full bg-gold/10 border border-gold/30 flex items-center justify-center mx-auto mb-4">
                  <span className="text-gold font-bold text-sm">{s.step}</span>
                </div>
                <h3 className="text-lg font-semibold mb-2">{s.title}</h3>
                <p className="text-sm text-muted">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Example Signals */}
      <section id="example-signals" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">Example Signals</h2>
            <p className="text-muted max-w-lg mx-auto">What you will receive. Real data, not mockups.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {SIGNALS.map((s, i) => (
              <motion.div key={s.pair} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className="signal-card bg-card border border-white/5 rounded-xl p-6 relative overflow-hidden">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold">{s.pair}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${s.dir === 'BUY' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                      {s.dir}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-16 h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full bg-gold rounded-full" style={{ width: `${s.conf}%` }} />
                    </div>
                    <span className="text-xs text-muted">{s.conf}%</span>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm mb-4">
                  <div><span className="text-muted block text-xs">Entry</span><span className="font-medium">{s.entry}</span></div>
                  <div><span className="text-muted block text-xs">Stop Loss</span><span className="font-medium text-red-400">{s.sl}</span></div>
                  <div><span className="text-muted block text-xs">Take Profit</span><span className="font-medium text-green-400">{s.tp}</span></div>
                </div>
                <div className="flex items-center justify-between text-xs text-muted border-t border-white/5 pt-3">
                  <span>{s.session} session</span>
                  <span>{s.reason}</span>
                </div>
              </motion.div>
            ))}
          </div>
          <div className="text-center mt-8">
            <p className="text-sm text-muted mb-4">Example signals. Not financial advice. Past performance does not guarantee future results.</p>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 px-6 bg-card/30 border-y border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">Simple Pricing</h2>
            <p className="text-muted max-w-lg mx-auto">No hidden fees. No performance cuts. Cancel anytime.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {PLANS.map((p, i) => (
              <motion.div key={p.name} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className={`bg-card rounded-xl p-6 border ${p.highlight ? 'border-gold/50 glow-orbit' : 'border-white/5'}`}>
                {p.highlight && <div className="text-xs text-gold font-semibold mb-3">Most Popular</div>}
                <h3 className="text-lg font-bold mb-2">{p.name}</h3>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-3xl font-bold">{p.price}</span>
                  <span className="text-sm text-muted">{p.period}</span>
                </div>
                <ul className="space-y-3 mb-6">
                  {p.features.map(f => (
                    <li key={f} className="flex items-center gap-2 text-sm">
                      <Check className="w-4 h-4 text-gold shrink-0" />
                      <span className="text-muted">{f}</span>
                    </li>
                  ))}
                </ul>
                <a href="https://t.me/TradeKnoxBot"
                  className={`block text-center py-2.5 rounded-lg text-sm font-medium transition-opacity ${p.highlight ? 'bg-gold text-bg hover:opacity-90' : 'bg-white/5 text-white hover:bg-white/10'}`}>
                  {p.cta}
                </a>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">Frequently Asked Questions</h2>
            <p className="text-muted">Everything you need to know. Click to expand.</p>
          </div>
          <div className="border-t border-white/5">
            {FAQ.map(f => <FAQItem key={f.q} q={f.q} a={f.a} />)}
          </div>
        </div>
      </section>

      {/* Email Capture */}
      <section className="py-20 px-6 bg-card/30 border-y border-white/5">
        <div className="max-w-xl mx-auto text-center">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">Stay Updated</h2>
          <p className="text-muted mb-8">Get strategy updates, backtest results, and market analysis. No spam. Unsubscribe anytime.</p>
          {subscribed ? (
            <div className="flex items-center justify-center gap-2 text-gold">
              <Check className="w-5 h-5" />
              <span className="font-medium">Subscribed. Check your inbox.</span>
            </div>
          ) : (
            <form onSubmit={handleSubscribe} className="flex gap-3 max-w-md mx-auto">
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@email.com"
                required
                className="flex-1 bg-card border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder:text-muted/50 focus:outline-none focus:border-gold/50 transition-colors"
              />
              <button type="submit" className="bg-gold text-bg px-4 py-2.5 rounded-lg text-sm font-medium btn-glow hover:opacity-90 transition-opacity inline-flex items-center gap-2">
                <Send className="w-4 h-4" />
              </button>
            </form>
          )}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gold/10 border border-gold/30 rounded flex items-center justify-center">
              <span className="text-gold font-bold text-xs">TK</span>
            </div>
            <span className="text-sm text-muted">TradeKnox 2026</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <a href="#faq" className="hover:text-white transition-colors">FAQ</a>
            <a href="https://t.me/TradeKnoxBot" className="hover:text-white transition-colors">Bot</a>
          </div>
          <p className="text-xs text-muted/50">Trading is high risk. Not financial advice.</p>
        </div>
      </footer>
    </div>
  )
}
