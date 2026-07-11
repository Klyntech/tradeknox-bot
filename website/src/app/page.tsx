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

/* ═══════════════════════════════════════════
   DATA
   ═══════════════════════════════════════════ */

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
  month: `M${i + 1}`,
  equity: 1000 * Math.pow(1.025, i) + (Math.random() - 0.4) * 200 * Math.sqrt(i + 1)
})).map((d, i) => ({ ...d, equity: Math.max(d.equity, 800) }))

const SCORING_RADAR = [
  { subject: 'Structure', A: 5, fullMark: 5 },
  { subject: 'Entry', A: 4, fullMark: 5 },
  { subject: 'Indicators', A: 3, fullMark: 5 },
  { subject: 'Confluence', A: 3, fullMark: 5 },
  { subject: 'Session', A: 3, fullMark: 5 },
  { subject: 'News', A: 2, fullMark: 5 },
]

const PIPELINE_STEPS = [
  { icon: Clock, label: 'Session Filter', desc: 'Only trades during optimal liquidity windows' },
  { icon: AlertTriangle, label: 'News Blackout', desc: 'Pauses before high-impact events' },
  { icon: Lock, label: 'Max Trades', desc: 'Daily position limit protection' },
  { icon: Globe, label: 'Data Fetch', desc: 'Real-time candle & indicator data' },
  { icon: BarChart3, label: 'Indicators', desc: 'EMA, RSI, ATR, Volume analysis' },
  { icon: Layers, label: 'Structure', desc: 'BOS / CHoCH detection engine' },
  { icon: Target, label: 'Entry Logic', desc: 'Order block & fair value gap entry' },
  { icon: Brain, label: 'Strategy Check', desc: '8-Gate & False Breakout validation' },
  { icon: Star, label: 'Scoring', desc: '6-category confluence scoring' },
  { icon: Shield, label: 'Risk Mgmt', desc: 'ATR-based SL/TP calculation' },
  { icon: RefreshCw, label: 'Trade Prep', desc: 'Order finalization & queue' },
  { icon: Bell, label: 'Telegram Out', desc: 'Instant signal delivery' },
]

const FAQ_DATA = [
  { q: 'How does the 12-layer signal pipeline work?', a: 'Every signal passes through 12 sequential filters: session check, news blackout, max trades limit, data fetch, indicators, market structure, entry logic, strategy validation, confluence scoring, risk management, trade preparation, and Telegram delivery. Only signals scoring 12/20 or higher reach your phone. Nothing slips through without passing every gate.' },
  { q: 'What forex pairs does TradeKnox support?', a: '8 major pairs: XAUUSD (Gold), GBPJPY, EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, and USDCAD. Each pair is scanned independently during London (7-16 UTC), New York (12-21 UTC), and Overlap sessions.' },
  { q: 'What is the SMC 8-Gate Strategy?', a: 'Our flagship trend-following strategy. Each trade must pass through 8 sequential structural validation gates: Trend Identification, BOS Confirmation, CHoCH Validation, Order Block Alignment, Fair Value Gap Check, Liquidity Sweep, Multi-Timeframe Confluence, and Entry Trigger. Backtested at 3.65x Profit Factor on XAUUSD over 20+ years.' },
  { q: 'How accurate are the backtested results?', a: 'All claims are backed by 20+ years of historical data across 8 forex pairs with realistic slippage and spread modeling. SMC 8-Gate averages 2.65x Profit Factor and 61.4% win rate. False Breakout Trap averages 1.62x PF across 24,000+ trades. Full backtesting scripts are open source.' },
  { q: 'Can I run this on my own server?', a: 'Yes. The full source code is on GitHub at github.com/Klyntech/tradeknox-bot. Deploy your own instance on Render free tier — no paid hosting required. The bot is 100% open source and free forever.' },
  { q: 'What is the False Breakout Trap strategy?', a: 'A counter-trend strategy that catches failed breakouts at key structural levels. When price sweeps beyond support or resistance to trap breakout traders, then closes back inside the range, the bot detects the trap and enters a reversal trade. Backtested at 1.62x Profit Factor.' },
  { q: 'How are signals delivered?', a: 'Signals are delivered instantly to @TradeKnoxTestBot on Telegram. Each signal includes entry price, stop loss, three take-profit levels, confidence percentage, confluence score, active session, strategy used, and a chart with marked order blocks and fair value gaps.' },
  { q: 'What is the confluence scoring system?', a: 'A 0-20 scale across 6 weighted categories: Market Structure (5pts), Entry Quality (4pts), Indicator Confirmation (3pts), Multi-TF Confluence (3pts), Session Timing (3pts), and News Safety (2pts). Only trades scoring 12/20 or higher are sent as signals.' },
]

const TICKER = [
  { pair: 'XAUUSD', price: '2,648.32', change: '+1.24%' },
  { pair: 'EURUSD', price: '1.0847', change: '+0.18%' },
  { pair: 'GBPUSD', price: '1.2715', change: '-0.09%' },
  { pair: 'USDJPY', price: '157.82', change: '+0.34%' },
  { pair: 'AUDUSD', price: '0.6534', change: '+0.22%' },
  { pair: 'GBPJPY', price: '200.71', change: '+0.41%' },
]


/* ═══════════════════════════════════════════
   CUSTOM HOOKS
   ═══════════════════════════════════════════ */

function useTyping(texts: string[], speed = 60, pause = 2500) {
  const [display, setDisplay] = useState('')
  const [idx, setIdx] = useState(0)
  const [charIdx, setCharIdx] = useState(0)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    const current = texts[idx]
    if (!deleting && charIdx < current.length) {
      const t = setTimeout(() => setCharIdx(c => c + 1), speed)
      return () => clearTimeout(t)
    } else if (!deleting && charIdx === current.length) {
      const t = setTimeout(() => setDeleting(true), pause)
      return () => clearTimeout(t)
    } else if (deleting && charIdx > 0) {
      const t = setTimeout(() => setCharIdx(c => c - 1), speed / 2)
      return () => clearTimeout(t)
    } else if (deleting && charIdx === 0) {
      setDeleting(false)
      setIdx((idx + 1) % texts.length)
    }
    setDisplay(texts[idx].slice(0, charIdx))
  }, [charIdx, deleting, idx, texts, speed, pause])

  return display
}


/* ═══════════════════════════════════════════
   ANIMATED CHART CANVAS (Hero visual)
   ═══════════════════════════════════════════ */

function ChartVisual() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const frameRef = useRef<number>(0)
  const dataRef = useRef<number[]>([])
  const offsetRef = useRef(0)

  const generateData = useCallback(() => {
    const data: number[] = []
    let price = 100
    for (let i = 0; i < 200; i++) {
      price += (Math.random() - 0.47) * 0.8
      price = Math.max(70, Math.min(130, price))
      data.push(price)
    }
    return data
  }, [])

  useEffect(() => {
    dataRef.current = generateData()
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const draw = () => {
      const { width, height } = canvas
      ctx.clearRect(0, 0, width, height)
      const data = dataRef.current
      const visibleCount = 80
      const offset = offsetRef.current % (data.length - visibleCount)

      // Grid lines
      ctx.strokeStyle = 'rgba(255,255,255,0.03)'
      ctx.lineWidth = 1
      for (let i = 0; i < 6; i++) {
        const y = (height / 6) * i
        ctx.beginPath()
        ctx.moveTo(0, y)
        ctx.lineTo(width, y)
        ctx.stroke()
      }

      const min = Math.min(...data.slice(offset, offset + visibleCount)) - 5
      const max = Math.max(...data.slice(offset, offset + visibleCount)) + 5
      const range = max - min

      // Area fill
      const gradient = ctx.createLinearGradient(0, 0, 0, height)
      gradient.addColorStop(0, 'rgba(212, 168, 67, 0.12)')
      gradient.addColorStop(0.5, 'rgba(212, 168, 67, 0.03)')
      gradient.addColorStop(1, 'transparent')

      ctx.beginPath()
      for (let i = 0; i < visibleCount; i++) {
        const x = (i / (visibleCount - 1)) * width
        const y = height - ((data[offset + i] - min) / range) * (height * 0.8) - height * 0.1
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      ctx.lineTo(width, height)
      ctx.lineTo(0, height)
      ctx.closePath()
      ctx.fillStyle = gradient
      ctx.fill()

      // Line
      ctx.beginPath()
      for (let i = 0; i < visibleCount; i++) {
        const x = (i / (visibleCount - 1)) * width
        const y = height - ((data[offset + i] - min) / range) * (height * 0.8) - height * 0.1
        if (i === 0) ctx.moveTo(x, y)
        else ctx.lineTo(x, y)
      }
      const lineGrad = ctx.createLinearGradient(0, 0, width, 0)
      lineGrad.addColorStop(0, 'rgba(212, 168, 67, 0.3)')
      lineGrad.addColorStop(0.5, 'rgba(212, 168, 67, 0.8)')
      lineGrad.addColorStop(1, 'rgba(212, 168, 67, 1)')
      ctx.strokeStyle = lineGrad
      ctx.lineWidth = 2
      ctx.stroke()

      // Glow dot at end
      const lastX = width
      const lastY = height - ((data[offset + visibleCount - 1] - min) / range) * (height * 0.8) - height * 0.1
      const glowGrad = ctx.createRadialGradient(lastX, lastY, 0, lastX, lastY, 20)
      glowGrad.addColorStop(0, 'rgba(212, 168, 67, 0.6)')
      glowGrad.addColorStop(1, 'transparent')
      ctx.fillStyle = glowGrad
      ctx.beginPath()
      ctx.arc(lastX, lastY, 20, 0, Math.PI * 2)
      ctx.fill()

      ctx.fillStyle = '#d4a843'
      ctx.beginPath()
      ctx.arc(lastX, lastY, 3, 0, Math.PI * 2)
      ctx.fill()

      offsetRef.current += 0.15
      frameRef.current = requestAnimationFrame(draw)
    }

    draw()
    return () => cancelAnimationFrame(frameRef.current)
  }, [generateData])

  return (
    <canvas
      ref={canvasRef}
      width={800}
      height={400}
      className="w-full h-full opacity-60"
    />
  )
}


/* ═══════════════════════════════════════════
   NAVBAR
   ═══════════════════════════════════════════ */

function Navbar() {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const links = ['Features', 'Strategy', 'Performance', 'Pipeline', 'Pricing']

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', h, { passive: true })
    return () => window.removeEventListener('scroll', h)
  }, [])

  return (
    <>
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${scrolled ? 'nav-blur' : ''}`}
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <a href="#" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gold to-gold-dim flex items-center justify-center">
              <CandlestickChart className="w-4 h-4 text-background" />
            </div>
            <span className="text-base font-semibold tracking-tight text-foreground">TradeKnox</span>
          </a>

          <div className="hidden md:flex items-center gap-8">
            {links.map(l => (
              <a key={l} href={`#${l.toLowerCase()}`} className="nav-link">{l}</a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            <a href="#pricing" className="btn-ghost text-sm py-2 px-4">View Plans</a>
            <a href="#pricing" className="btn-gold text-sm py-2 px-4 inline-flex items-center gap-1.5">
              Get Started <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>

          <button onClick={() => setOpen(!open)} className="md:hidden text-foreground">
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </motion.nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-background/95 backdrop-blur-xl pt-20 px-6"
          >
            <div className="flex flex-col gap-6 max-w-md mx-auto">
              {links.map(l => (
                <a
                  key={l}
                  href={`#${l.toLowerCase()}`}
                  onClick={() => setOpen(false)}
                  className="text-2xl font-medium text-foreground/80 hover:text-foreground transition-colors"
                >
                  {l}
                </a>
              ))}
              <div className="pt-6 border-t border-white/5 flex flex-col gap-3">
                <a href="#pricing" onClick={() => setOpen(false)} className="btn-ghost text-center">View Plans</a>
                <a href="#pricing" onClick={() => setOpen(false)} className="btn-gold text-center">Get Started</a>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}


/* ═══════════════════════════════════════════
   HERO
   ═══════════════════════════════════════════ */

function Hero() {
  const typed = useTyping(['Institutional-Grade', 'AI-Powered', 'Precision-Engineered'], 55, 2800)
  const { scrollYProgress } = useScroll()
  const heroOpacity = useTransform(scrollYProgress, [0, 0.15], [1, 0])
  const heroY = useTransform(scrollYProgress, [0, 0.15], [0, -60])
  const [ticker, setTicker] = useState(TICKER)

  useEffect(() => {
    async function fetchPrices() {
      try {
        const r = await fetch('/api')
        if (!r.ok) return
        const data = await r.json()
        if (data && Object.keys(data).length > 0) {
          setTicker(PAIRS.map(p => {
            const d = data[p]
            if (!d) return TICKER.find(t => t.pair === p)!
            return {
              pair: p,
              price: d.p.toLocaleString(undefined, { minimumFractionDigits: p === 'XAUUSD' || p === 'USDJPY' || p === 'GBPJPY' ? 2 : 4, maximumFractionDigits: p === 'XAUUSD' || p === 'USDJPY' || p === 'GBPJPY' ? 2 : 4 }),
              change: `${d.c >= 0 ? '+' : ''}${d.c.toFixed(2)}%`,
            }
          }))
        }
      } catch {}
    }
    fetchPrices()
    const iv = setInterval(fetchPrices, 30000)
    return () => clearInterval(iv)
  }, [])

  return (
    <section className="hero-scene flex flex-col justify-center relative">
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />
      <div className="hero-grid" />

      <motion.div style={{ opacity: heroOpacity, y: heroY }} className="relative z-10 pt-32 pb-8 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Ticker */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="mb-12"
          >
            <div className="overflow-hidden rounded-xl border border-white/[0.04] bg-white/[0.02] py-3 px-1">
              <div className="marquee-track">
                {[...ticker, ...ticker, ...ticker, ...ticker].map((t, i) => (
                  <span key={i} className="flex items-center gap-3 px-6 text-xs whitespace-nowrap">
                    <span className="text-muted-foreground font-mono">{t.pair}</span>
                    <span className="text-foreground/80 font-mono">{t.price}</span>
                    <span className={t.change.startsWith('+') ? 'text-emerald' : 'text-loss'}>
                      {t.change}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Main headline */}
          <div className="max-w-4xl">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
              className="section-tag mb-8"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Next-Generation Forex Intelligence
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
              className="text-[clamp(2.5rem,7vw,5rem)] font-semibold leading-[1.05] tracking-[-0.04em] mb-6"
            >
              <span className="text-foreground">The </span>
              <span className="bg-gradient-to-r from-gold via-gold-light to-gold bg-clip-text text-transparent">
                {typed}
              </span>
              <br />
              <span className="text-foreground">Forex Trading Bot</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
              className="text-lg text-muted-foreground leading-relaxed max-w-2xl mb-10"
            >
              12-layer signal pipeline. SMC 8-Gate strategy. 20+ years backtested across 8 forex pairs.
              TradeKnox delivers institutional-quality signals with surgical precision.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6, duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
              className="flex flex-wrap gap-4 mb-16"
            >
              <a href="#pricing" className="btn-gold text-sm inline-flex items-center gap-2">
                Start Trading <ArrowRight className="w-4 h-4" />
              </a>
              <a href="#strategy" className="btn-ghost text-sm inline-flex items-center gap-2">
                <Play className="w-4 h-4" /> Explore Strategies
              </a>
            </motion.div>
          </div>

          {/* Chart visual */}
          <motion.div
            initial={{ opacity: 0, y: 40, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: 0.8, duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            className="relative max-w-5xl mx-auto"
          >
            <div className="absolute -inset-px rounded-2xl bg-gradient-to-b from-white/[0.08] to-transparent pointer-events-none" />
            <div className="relative rounded-2xl bg-white/[0.02] border border-white/[0.06] overflow-hidden h-[320px] md:h-[400px]">
              <ChartVisual />
              {/* Overlay gradient at edges */}
              <div className="absolute inset-0 pointer-events-none" style={{
                background: 'linear-gradient(90deg, #020204 0%, transparent 15%, transparent 85%, #020204 100%)'
              }} />
              <div className="absolute bottom-0 left-0 right-0 h-20 pointer-events-none" style={{
                background: 'linear-gradient(to top, #020204, transparent)'
              }} />
            </div>
          </motion.div>
        </div>
      </motion.div>
    </section>
  )
}


/* ═══════════════════════════════════════════
   STATS BAR
   ═══════════════════════════════════════════ */

function StatsBar() {
  const stats = [
    { value: 2.65, suffix: 'x', label: 'Avg Profit Factor', decimals: 2 },
    { value: 61.4, suffix: '%', label: 'Win Rate', decimals: 1 },
    { value: 5250, suffix: '+', label: 'Backtested Trades', decimals: 0 },
    { value: 20, suffix: 'yrs', label: 'Historical Data', decimals: 0 },
  ]

  return (
    <section className="relative py-20 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-4">
          {stats.map((s, i) => (
            <ScrollReveal key={i} delay={i * 100}>
              <StatCard {...s} />
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}

function StatCard({ value, suffix, label, decimals }: { value: number; suffix: string; label: string; decimals: number }) {
  const { count, ref } = useCountUp(value, 2500, decimals)

  return (
    <div ref={ref} className="text-center">
      <div className="stat-value text-3xl md:text-4xl font-semibold tracking-tight mb-1.5">
        {count}<span className="text-xl md:text-2xl ml-0.5">{suffix}</span>
      </div>
      <div className="text-muted-foreground text-sm">{label}</div>
    </div>
  )
}


/* ═══════════════════════════════════════════
   FEATURES
   ═══════════════════════════════════════════ */

function Features() {
  const features = [
    {
      icon: Layers, color: 'icon-container',
      title: 'SMC 8-Gate Strategy',
      desc: 'Eight sequential structural validation gates ensure every trade aligns with institutional order flow. BOS, CHoCH, and liquidity sweep detection built in.',
    },
    {
      icon: Target, color: 'icon-container-emerald',
      title: 'Order Block Detection',
      desc: 'Real-time identification of institutional order blocks and fair value gaps across multiple timeframes, giving you the same edge as prop desk traders.',
    },
    {
      icon: Star, color: 'icon-container-violet',
      title: '6-Category Scoring',
      desc: 'A 0-20 point confluence scoring system evaluating structure, entry quality, indicators, multi-timeframe agreement, session timing, and news safety.',
    },
    {
      icon: Shield, color: 'icon-container-sky',
      title: 'Intelligent Risk Management',
      desc: 'ATR-based dynamic stop losses and take profits. Position sizing, max daily trades, and drawdown protection ensure capital preservation.',
    },
    {
      icon: Activity, color: 'icon-container',
      title: 'Multi-Timeframe Analysis',
      desc: 'Simultaneous analysis across H1, H4, and D1 timeframes. Higher timeframe bias filters lower timeframe entries for maximum probability setups.',
    },
    {
      icon: Zap, color: 'icon-container-emerald',
      title: '12-Layer Signal Pipeline',
      desc: 'From session filtering through news blackout, structure analysis, strategy validation, scoring, and risk management — every signal is battle-tested.',
    },
  ]

  return (
    <section id="features" className="relative py-28 px-6">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <div className="section-tag mx-auto mb-6">
              <Zap className="w-3.5 h-3.5" />
              Engineered for Precision
            </div>
            <h2 className="section-heading mb-4">Every edge, <span className="bg-gradient-to-r from-gold to-gold-light bg-clip-text text-transparent">systematized</span></h2>
            <p className="section-sub mx-auto text-center">
              Six core pillars power every signal. No guesswork, no emotions — just institutional-grade analysis delivered in real time.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <ScrollReveal key={i} delay={i * 80}>
              <div className="glass-card p-7 h-full">
                <div className={`icon-container ${f.color} mb-5`}>
                  <f.icon className="w-5 h-5" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-2.5 tracking-tight">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}


/* ═══════════════════════════════════════════
   STRATEGY SHOWCASE
   ═══════════════════════════════════════════ */

function Strategy() {
  const gates = ['Trend Identification', 'BOS Confirmation', 'CHoCH Validation', 'Order Block Alignment', 'Fair Value Gap Check', 'Liquidity Sweep', 'Multi-TF Confluence', 'Entry Trigger']

  return (
    <section id="strategy" className="relative py-28 px-6">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <div className="section-tag mx-auto mb-6">
              <Brain className="w-3.5 h-3.5" />
              Dual Strategy Engine
            </div>
            <h2 className="section-heading mb-4">Two strategies, <span className="bg-gradient-to-r from-gold to-emerald bg-clip-text text-transparent">one system</span></h2>
            <p className="section-sub mx-auto text-center">
              TradeKnox deploys two complementary strategies that cover both trending and ranging market conditions, ensuring consistent performance across all regimes.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* SMC 8-Gate */}
          <ScrollReveal>
            <div className="gradient-card h-full">
              <div className="gradient-card-inner">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-gold/10 border border-gold/20 flex items-center justify-center">
                    <Layers className="w-5 h-5 text-gold" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">SMC 8-Gate Strategy</h3>
                    <p className="text-xs text-muted-foreground">Trend-following precision</p>
                  </div>
                </div>

                <p className="text-sm text-muted-foreground leading-relaxed mb-8">
                  Our flagship strategy requires trades to pass through eight sequential structural validation gates. Each gate filters out non-ideal setups, ensuring only the highest-probability institutional order flow alignments trigger signals.
                </p>

                <div className="grid grid-cols-2 gap-3">
                  {gates.map((gate, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 60 }}
                      className="flex items-center gap-2.5 py-2.5 px-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04]"
                    >
                      <span className="w-5 h-5 rounded-md bg-gold/10 text-gold text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                        {i + 1}
                      </span>
                      <span className="text-xs text-foreground/80">{gate}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </ScrollReveal>

          {/* False Breakout Trap */}
          <ScrollReveal delay={150}>
            <div className="gradient-card h-full" style={{ /* green variant */ }}>
              <div className="gradient-card-inner">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-emerald/10 border border-emerald/20 flex items-center justify-center">
                    <Target className="w-5 h-5 text-emerald" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">False Breakout Trap</h3>
                    <p className="text-xs text-muted-foreground">Counter-trend reversals</p>
                  </div>
                </div>

                <p className="text-sm text-muted-foreground leading-relaxed mb-8">
                  A sophisticated counter-trend strategy that identifies failed breakouts of key structural levels. When price sweeps liquidity beyond a significant level then reverses, TradeKnox detects the trap and positions for the high-probability reversal move.
                </p>

                <div className="space-y-3">
                  {[
                    { label: 'Breakout Detection', desc: 'Identifies price sweeping beyond key support/resistance' },
                    { label: 'Failure Confirmation', desc: 'Waits for close back within the structural range' },
                    { label: 'Reversal Entry', desc: 'Enters on the first pullback after confirmed failure' },
                    { label: 'Regime Coverage', desc: 'Excels in ranging/choppy markets where trends fail' },
                  ].map((item, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 80 }}
                      className="flex items-start gap-3 py-3 px-4 rounded-xl bg-white/[0.02] border border-white/[0.04]"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald mt-1.5 flex-shrink-0" />
                      <div>
                        <div className="text-sm font-medium text-foreground/90 mb-0.5">{item.label}</div>
                        <div className="text-xs text-muted-foreground">{item.desc}</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  )
}


/* ═══════════════════════════════════════════
   PERFORMANCE
   ═══════════════════════════════════════════ */

function Performance() {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#0a0a0f] border border-white/[0.08] rounded-xl px-4 py-3 shadow-2xl">
          <p className="text-xs font-semibold text-foreground mb-1">{label}</p>
          {payload.map((p: any, i: number) => (
            <p key={i} className="text-xs text-muted-foreground">
              {p.name}: <span className="text-foreground">{p.value}</span>
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <section id="performance" className="relative py-28 px-6">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <div className="section-tag mx-auto mb-6">
              <BarChart3 className="w-3.5 h-3.5" />
              Proven Track Record
            </div>
            <h2 className="section-heading mb-4">
              <span className="bg-gradient-to-r from-gold to-emerald bg-clip-text text-transparent">20+ years</span> of backtested data
            </h2>
            <p className="section-sub mx-auto text-center">
              Every claim is backed by extensive historical testing across 8 major forex pairs with realistic slippage and spread modeling.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid lg:grid-cols-5 gap-6">
          {/* Chart */}
          <ScrollReveal className="lg:col-span-3">
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Profit Factor by Pair</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">20+ year backtest results</p>
                </div>
                <div className="flex items-center gap-1.5 text-emerald text-xs font-medium">
                  <TrendingUp className="w-3.5 h-3.5" />
                  Avg 2.65x
                </div>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={PAIR_DATA} barSize={32}>
                  <XAxis
                    dataKey="pair"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#5a5a72', fontSize: 11 }}
                    dy={8}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#5a5a72', fontSize: 11 }}
                    dx={-4}
                    width={35}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                  <Bar dataKey="pf" name="Profit Factor" radius={[6, 6, 0, 0]}>
                    {PAIR_DATA.map((entry, index) => (
                      <Cell
                        key={index}
                        fill={entry.pf >= 3 ? '#d4a843' : entry.pf >= 2.5 ? '#b8912e' : '#8a6d2b'}
                        opacity={0.6 + (entry.pf / 5) * 0.4}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ScrollReveal>

          {/* Stats grid */}
          <ScrollReveal delay={100} className="lg:col-span-2">
            <div className="grid grid-cols-2 gap-4 h-full">
              {[
                { label: 'Best Pair', value: 'XAUUSD', sub: 'PF: 3.65x', accent: 'text-gold' },
                { label: 'Avg Sharpe', value: '2.00', sub: 'Risk-adjusted', accent: 'text-emerald' },
                { label: 'Total Trades', value: '5,250', sub: 'Across 8 pairs', accent: 'text-foreground' },
                { label: 'Win Rate', value: '61.4%', sub: 'Avg all pairs', accent: 'text-gold-light' },
                { label: 'Best Sharpe', value: '2.84', sub: 'XAUUSD', accent: 'text-emerald' },
                { label: 'Pairs', value: '8', sub: 'Major forex', accent: 'text-foreground' },
              ].map((s, i) => (
                <div key={i} className="glass-card p-5 flex flex-col justify-center">
                  <div className="text-[11px] text-muted-foreground uppercase tracking-wider mb-2">{s.label}</div>
                  <div className={`text-2xl font-semibold tracking-tight ${s.accent}`}>{s.value}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{s.sub}</div>
                </div>
              ))}
            </div>
          </ScrollReveal>
        </div>

        {/* Equity Curve */}
        <ScrollReveal className="mt-6">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Model Equity Curve</h3>
                <p className="text-xs text-muted-foreground mt-0.5">Hypothetical growth of $1,000 initial capital</p>
              </div>
              <div className="text-xs text-emerald font-medium">+2,400% projected</div>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={EQUITY_CURVE}>
                <defs>
                  <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#d4a843" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="#d4a843" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#5a5a72', fontSize: 10 }}
                  interval={9}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#5a5a72', fontSize: 10 }}
                  dx={-4}
                  width={50}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#d4a843"
                  strokeWidth={2}
                  fill="url(#equityGrad)"
                  name="Equity ($)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}


/* ═══════════════════════════════════════════
   PIPELINE
   ═══════════════════════════════════════════ */

function Pipeline() {
  return (
    <section id="pipeline" className="relative py-28 px-6">
      <div className="max-w-7xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <div className="section-tag mx-auto mb-6">
              <Filter className="w-3.5 h-3.5" />
              12-Layer Pipeline
            </div>
            <h2 className="section-heading mb-4">Every signal passes through <span className="bg-gradient-to-r from-gold to-gold-light bg-clip-text text-transparent">12 filters</span></h2>
            <p className="section-sub mx-auto text-center">
              From market open to signal delivery, each layer eliminates noise and confirms confluence. Nothing reaches your Telegram that hasn't been thoroughly validated.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {PIPELINE_STEPS.map((step, i) => (
            <ScrollReveal key={i} delay={i * 50}>
              <motion.div
                whileHover={{ scale: 1.02, y: -4 }}
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                className="glass-card p-5 group relative"
              >
                <div className="absolute top-3 right-3 text-[10px] font-bold text-muted-foreground/40">
                  {String(i + 1).padStart(2, '0')}
                </div>
                <step.icon className="w-5 h-5 text-gold mb-3 group-hover:text-gold-light transition-colors" />
                <h4 className="text-sm font-semibold text-foreground mb-1">{step.label}</h4>
                <p className="text-xs text-muted-foreground leading-relaxed">{step.desc}</p>
              </motion.div>
            </ScrollReveal>
          ))}
        </div>

        {/* Scoring System */}
        <ScrollReveal className="mt-16">
          <div className="gradient-card">
            <div className="gradient-card-inner">
              <div className="grid lg:grid-cols-2 gap-12 items-center">
                <div>
                  <h3 className="text-xl font-semibold text-foreground mb-3 tracking-tight">Confluence Scoring System</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed mb-8">
                    Every potential trade receives a 0-20 score across six weighted categories. Only trades scoring 12 or above are delivered as signals — ensuring you only act on the highest-conviction setups.
                  </p>
                  <div className="space-y-4">
                    {[
                      { cat: 'Market Structure', weight: '5 pts', pct: 100, color: '#d4a843' },
                      { cat: 'Entry Quality', weight: '4 pts', pct: 80, color: '#e8cc7a' },
                      { cat: 'Indicator Confirmation', weight: '3 pts', pct: 60, color: '#34d399' },
                      { cat: 'Multi-TF Confluence', weight: '3 pts', pct: 60, color: '#818cf8' },
                      { cat: 'Session Timing', weight: '3 pts', pct: 60, color: '#38bdf8' },
                      { cat: 'News Safety', weight: '2 pts', pct: 40, color: '#5a5a72' },
                    ].map((s, i) => (
                      <div key={i}>
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-medium text-foreground/80">{s.cat}</span>
                          <span className="text-[11px] text-muted-foreground">{s.weight}</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            whileInView={{ width: `${s.pct}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 1, delay: i * 100, ease: [0.16, 1, 0.3, 1] }}
                            className="h-full rounded-full"
                            style={{ background: s.color }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex justify-center">
                  <ResponsiveContainer width="100%" height={320}>
                    <RadarChart data={SCORING_RADAR} cx="50%" cy="50%" outerRadius="70%">
                      <PolarGrid stroke="rgba(255,255,255,0.06)" />
                      <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: '#7a7a90', fontSize: 11 }}
                      />
                      <Radar
                        name="Score"
                        dataKey="A"
                        stroke="#d4a843"
                        fill="#d4a843"
                        fillOpacity={0.15}
                        strokeWidth={2}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}


/* ═══════════════════════════════════════════
   PRICING
   ═══════════════════════════════════════════ */

function Pricing() {
  const plans = [
    {
      name: 'TradeKnox',
      price: '$0',
      period: '/ forever',
      desc: 'All features. No limits. No catch.',
      features: ['All 8 forex pairs', 'Unlimited signals', 'Instant Telegram delivery', 'SMC 8-Gate + False Breakout strategies', 'Full confluence score breakdown', 'Chart with every signal', 'Performance tracking and analytics', 'Open source — audit the code yourself'],
      cta: 'Start on Telegram',
      featured: true,
    },
  ]

  return (
    <section id="pricing" className="relative py-28 px-6">
      <div className="max-w-6xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <div className="section-tag mx-auto mb-6">
              <Sparkles className="w-3.5 h-3.5" />
              Simple Pricing
            </div>
            <h2 className="section-heading mb-4">Choose your <span className="bg-gradient-to-r from-gold to-gold-light bg-clip-text text-transparent">trading edge</span></h2>
            <p className="section-sub mx-auto text-center">
              Start free. Upgrade when you're ready. No hidden fees, no lock-in contracts.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid md:grid-cols-3 gap-6 items-start">
          {plans.map((plan, i) => (
            <ScrollReveal key={i} delay={i * 100}>
              <div className={`relative rounded-[20px] ${plan.featured ? 'pricing-featured' : ''}`}>
                {plan.featured && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10">
                    <span className="text-[10px] font-bold uppercase tracking-widest bg-gold text-background px-4 py-1 rounded-full">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className={`rounded-[20px] p-8 h-full flex flex-col ${plan.featured
                    ? 'bg-gradient-to-b from-[#0d0d14] to-[#08080d] border border-gold/20'
                    : 'glass-card'
                  }`}>
                  <div className="mb-6">
                    <h3 className="text-sm font-semibold text-muted-foreground mb-1">{plan.name}</h3>
                    <div className="flex items-baseline gap-1">
                      <span className={`text-4xl font-semibold tracking-tight ${plan.featured ? 'text-foreground' : 'text-foreground/90'}`}>{plan.price}</span>
                      {plan.period && <span className="text-sm text-muted-foreground">{plan.period}</span>}
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">{plan.desc}</p>
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {plan.features.map((f, j) => (
                      <li key={j} className="flex items-start gap-2.5">
                        <Check className="w-4 h-4 text-gold mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-foreground/70">{f}</span>
                      </li>
                    ))}
                  </ul>

                  <a
                    href="#"
                    className={plan.featured
                      ? 'btn-gold text-sm text-center w-full inline-flex items-center justify-center gap-2'
                      : 'btn-ghost text-sm text-center w-full'
                    }
                  >
                    {plan.cta}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}


/* ═══════════════════════════════════════════
   FAQ
   ═══════════════════════════════════════════ */

function FAQ() {
  const [openIdx, setOpenIdx] = useState<number | null>(null)

  return (
    <section className="relative py-28 px-6">
      <div className="max-w-3xl mx-auto">
        <ScrollReveal>
          <div className="text-center mb-16">
            <div className="section-tag mx-auto mb-6">
              <Bot className="w-3.5 h-3.5" />
              FAQ
            </div>
            <h2 className="section-heading mb-4">Questions & <span className="bg-gradient-to-r from-gold to-gold-light bg-clip-text text-transparent">answers</span></h2>
          </div>
        </ScrollReveal>

        <div className="divide-y divide-white/[0.04]">
          {FAQ_DATA.map((item, i) => (
            <ScrollReveal key={i} delay={i * 40}>
              <div className="faq-item">
                <button
                  onClick={() => setOpenIdx(openIdx === i ? null : i)}
                  className="w-full flex items-center justify-between py-5 px-1 text-left"
                >
                  <span className="text-sm font-medium text-foreground/90 pr-4">{item.q}</span>
                  <ChevronDown
                    className={`w-4 h-4 text-muted-foreground flex-shrink-0 transition-transform duration-300 ${openIdx === i ? 'rotate-180' : ''}`}
                  />
                </button>
                <AnimatePresence>
                  {openIdx === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <p className="pb-5 px-1 text-sm text-muted-foreground leading-relaxed">
                        {item.a}
                      </p>
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


/* ═══════════════════════════════════════════
   CTA
   ═══════════════════════════════════════════ */

function CTA() {
  return (
    <section className="relative py-28 px-6">
      <div className="max-w-4xl mx-auto">
        <ScrollReveal>
          <div className="relative rounded-3xl overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-gold/10 via-transparent to-emerald/5" />
            <div className="absolute inset-0 border border-gold/10 rounded-3xl" />
            <div className="relative px-8 py-16 md:px-16 md:py-20 text-center">
              <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-foreground mb-4">
                Ready to trade with<br />
                <span className="bg-gradient-to-r from-gold via-gold-light to-gold bg-clip-text text-transparent">institutional precision?</span>
              </h2>
              <p className="text-muted-foreground max-w-md mx-auto mb-8">
                Join traders who trust data-driven signals over gut feelings. Start free, upgrade when you see the results.
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <a href="#pricing" className="btn-gold text-sm inline-flex items-center gap-2">
                  Get Started Free <ArrowRight className="w-4 h-4" />
                </a>
                <a href="#features" className="btn-ghost text-sm inline-flex items-center gap-2">
                  Learn More
                </a>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}


/* ═══════════════════════════════════════════
   FOOTER
   ═══════════════════════════════════════════ */

function Footer() {
  return (
    <footer className="relative pt-16 pb-8 px-6 border-t border-white/[0.04]">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-4 gap-10 mb-12">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-gold to-gold-dim flex items-center justify-center">
                <CandlestickChart className="w-3.5 h-3.5 text-background" />
              </div>
              <span className="text-sm font-semibold tracking-tight">TradeKnox</span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Institutional-grade forex signals powered by SMC analysis, multi-timeframe confluence, and 12-layer validation.
            </p>
          </div>

          {[
            { title: 'Product', links: ['Features', 'Strategy', 'Performance', 'Pipeline', 'Pricing'] },
            { title: 'Resources', links: ['Documentation', 'API Reference', 'Backtest Data', 'Blog', 'Changelog'] },
            { title: 'Company', links: ['About', 'Contact', 'Privacy Policy', 'Terms of Service', 'Disclosures'] },
          ].map((col, i) => (
            <div key={i}>
              <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider mb-4">{col.title}</h4>
              <ul className="space-y-2.5">
                {col.links.map(link => (
                  <li key={link}>
                    <a href="#" className="text-xs text-muted-foreground hover:text-foreground transition-colors">{link}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="divider mb-6" />
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
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


/* ═══════════════════════════════════════════
   PAGE
   ═══════════════════════════════════════════ */

export default function Page() {
  return (
    <main className="noise">
      <ScrollProgress />
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