import { useState } from 'react'

// ─── API URL ────────────────────────────────────────────────────────────────
const API_URL = import.meta.env.VITE_API_URL || ''

// ─── CONSTANTS ───────────────────────────────────────────────────────────────
const PIPELINE_TOOLS = [
    { key: 'tool_signal_harvester', icon: '📡', label: 'Signal Harvester', desc: 'Grounded Google Search', color: 'blue' },
    { key: 'tool_research_analyst', icon: '🔬', label: 'Research Analyst', desc: 'AI Account Brief', color: 'purple' },
    { key: 'tool_outreach_automated_sender', icon: '📧', label: 'Email Generator', desc: 'Personalized Email', color: 'green' },
]

const STEP_COLORS = {
    blue: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-400' },
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', dot: 'bg-purple-400' },
    green: { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', dot: 'bg-green-400' },
}

// ─── HELPERS ─────────────────────────────────────────────────────────────────
function getStepForTool(steps, toolKey) {
    return steps?.find((s) => s.tool === toolKey)
}

function getStatusBadge(step, toolKey, steps, liveSteps, progress) {
    const allSteps = steps?.length > 0 ? steps : (liveSteps || [])
    if (!allSteps || allSteps.length === 0) {
        if (progress && progress.tool === toolKey) return 'running'
        return 'pending'
    }
    const found = allSteps.find((s) => s.tool === toolKey)
    if (!found) {
        if (progress && progress.tool === toolKey) return 'running'
        return 'pending'
    }
    return found.status === 'completed' ? 'done' : 'error'
}

// ─── SUB-COMPONENTS ──────────────────────────────────────────────────────────

/** Single pipeline step indicator */
function PipelineStep({ tool, status }) {
    const colors = STEP_COLORS[tool.color]
    const isActive = status === 'done'
    const isRunning = status === 'running'
    const isError = status === 'error'

    return (
        <div className={`relative flex-1 rounded-xl border p-3 transition-all duration-500 ${isError ? 'bg-red-500/10 border-red-500/30' :
            isRunning ? `${colors.bg} ${colors.border}` :
            isActive ? `${colors.bg} ${colors.border}` : 'bg-gray-900/50 border-gray-700/30'
            }`}>
            <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{tool.icon}</span>
                <div className="flex-1 min-w-0">
                    <p className={`text-xs font-semibold truncate ${isError ? 'text-red-400' : isRunning ? 'text-orange-400' : isActive ? colors.text : 'text-gray-400'}`}>{tool.label}</p>
                    <p className="text-[10px] text-gray-500 truncate">{tool.desc}</p>
                </div>
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${isError ? 'bg-red-400' : isRunning ? 'bg-orange-400 animate-pulse shadow-lg shadow-orange-500/50' : isActive ? `${colors.dot} shadow-lg` : 'bg-gray-600'} ${isActive || isRunning ? 'animate-pulse' : ''}`} />
            </div>
            <div className={`text-[10px] font-mono px-1.5 py-0.5 rounded inline-block ${isError ? 'bg-red-500/20 text-red-300' : isRunning ? 'bg-orange-500/20 text-orange-300' : isActive ? 'bg-gray-900/60 text-gray-300' : 'bg-gray-800/40 text-gray-500'}`}>
                {isError ? 'error' : isRunning ? 'running…' : isActive ? 'done' : 'pending'}
            </div>
        </div>
    )
}

// ─── SIGNAL CATEGORIES ───────────────────────────────────────────────────────
const CAT_COLORS = {
    funding: 'text-yellow-400', hiring: 'text-blue-400', leadership: 'text-purple-400',
    news: 'text-green-400', tech_stack: 'text-cyan-400', g2_reviews: 'text-pink-400',
    social_mentions: 'text-sky-400', competitor_churn: 'text-orange-400',
}
const CAT_ICONS = {
    funding: '💰', hiring: '👥', leadership: '👔', news: '📰',
    tech_stack: '⚙️', g2_reviews: '⭐', social_mentions: '📣', competitor_churn: '🔄',
}

// ─── RESULT SECTION COMPONENTS ───────────────────────────────────────────────

/** Signals section — shows harvested buyer signals */
function SignalSection({ step }) {
    const signals = step?.result?.signals || {}
    const entries = Object.entries(signals).filter(([, v]) => v?.length > 0)
    if (!entries.length) return <p className="text-gray-500 text-sm italic">No signals captured.</p>

    return (
        <div className="glass-card rounded-2xl p-5 border border-blue-500/20 animate-slide-up">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <span className="text-xl">📡</span>
                    <h3 className="text-sm font-bold text-blue-400">Buyer Signals</h3>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${step?.result?.mode === 'grounded_search' ? 'bg-green-500/20 text-green-300' : 'bg-yellow-500/20 text-yellow-300'}`}>
                        {step?.result?.mode === 'grounded_search' ? '🌐 Live Search' : '🎭 Demo'}
                    </span>
                    {step?.result?.sources_count > 0 && (
                        <span className="text-[10px] text-gray-500">{step.result.sources_count} sources</span>
                    )}
                </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {entries.map(([cat, findings]) => (
                    <div key={cat} className="p-3 rounded-xl bg-gray-900/60 border border-gray-700/20">
                        <p className={`text-[10px] font-bold uppercase tracking-wider mb-2 flex items-center gap-1.5 ${CAT_COLORS[cat] || 'text-gray-400'}`}>
                            <span>{CAT_ICONS[cat] || '📌'}</span>{cat.replace(/_/g, ' ')}
                            <span className="ml-auto text-gray-600 font-normal">{findings.length}</span>
                        </p>
                        {findings.slice(0, 3).map((f, i) => (
                            <div key={i} className="mb-1.5 last:mb-0">
                                <p className="text-xs text-gray-300 leading-relaxed">{f.finding}</p>
                                {f.source_url && (
                                    <a href={f.source_url} target="_blank" rel="noreferrer"
                                        className="text-[10px] text-orange-400/50 hover:text-orange-400 truncate block max-w-xs">
                                        {f.source_title || f.source_url}
                                    </a>
                                )}
                            </div>
                        ))}
                    </div>
                ))}
            </div>
        </div>
    )
}

/** Research section — account brief & pain points */
function ResearchSection({ step }) {
    const res = step?.result || {}
    if (!res.account_brief && !res.recommended_angle) return null

    return (
        <div className="glass-card rounded-2xl p-5 border border-purple-500/20 animate-slide-up">
            <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">🔬</span>
                <h3 className="text-sm font-bold text-purple-400">Account Brief</h3>
                <div className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 font-medium">
                    {step?.status}
                </div>
            </div>
            {res.account_brief && (
                <div className="mb-4 p-3 rounded-xl bg-gray-900/60 border border-gray-700/20">
                    <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-line">{res.account_brief}</p>
                </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {res.key_signals_identified?.length > 0 && (
                    <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-700/20">
                        <p className="text-[10px] font-bold text-purple-400 uppercase tracking-wider mb-2">Key Signals</p>
                        <ul className="space-y-1">
                            {res.key_signals_identified.map((s, i) => (
                                <li key={i} className="flex gap-2 text-xs text-gray-300">
                                    <span className="text-purple-400 flex-shrink-0">→</span>
                                    <span>{s}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
                {res.pain_points?.length > 0 && (
                    <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-700/20">
                        <p className="text-[10px] font-bold text-red-400 uppercase tracking-wider mb-2">Pain Points</p>
                        <ul className="space-y-1">
                            {res.pain_points.map((p, i) => (
                                <li key={i} className="flex gap-2 text-xs text-gray-300">
                                    <span className="text-red-400 flex-shrink-0">!</span>
                                    <span>{p}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
            {res.recommended_angle && (
                <div className="mt-3 p-3 rounded-xl bg-orange-500/5 border border-orange-500/15">
                    <p className="text-[10px] font-bold text-orange-400 uppercase tracking-wider mb-1">Recommended Angle</p>
                    <p className="text-xs text-gray-200 italic leading-relaxed">{res.recommended_angle}</p>
                </div>
            )}
        </div>
    )
}

/** Email section — the generated email (main output) */
function EmailSection({ step }) {
    const email = step?.result?.email
    const sendStatus = step?.result?.send_status
    if (!email?.subject) return null

    return (
        <div className="glass-card rounded-2xl p-5 border border-green-500/20 animate-slide-up">
            <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">📧</span>
                <h3 className="text-sm font-bold text-green-400">Generated Email</h3>
                {sendStatus && (
                    <div className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-medium ${sendStatus.success ? 'bg-green-500/10 text-green-300' : 'bg-blue-500/10 text-blue-300'}`}>
                        {sendStatus.method === 'preview_only' ? '👁️ Preview' : sendStatus.success ? '✅ Sent' : '⚠️ Not Sent'}
                    </div>
                )}
            </div>
            {/* Subject */}
            <div className="mb-3 p-3 rounded-xl bg-orange-500/5 border border-orange-500/15">
                <p className="text-[10px] font-mono text-gray-500 mb-1">SUBJECT</p>
                <p className="text-sm font-semibold text-orange-300">{email.subject}</p>
            </div>
            {/* Body */}
            <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-700/20 mb-3">
                <pre className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed font-sans">{email.body}</pre>
            </div>
            {/* Send Status Detail */}
            {sendStatus && (
                <div className={`flex items-center gap-3 p-3 rounded-xl text-xs ${sendStatus.method === 'preview_only' ? 'bg-blue-500/5 border border-blue-500/15 text-blue-300' :
                    sendStatus.success ? 'bg-green-500/5 border border-green-500/15 text-green-300' :
                        'bg-yellow-500/5 border border-yellow-500/15 text-yellow-300'
                    }`}>
                    <span className="text-base">
                        {sendStatus.method === 'preview_only' ? '👁️' : sendStatus.success ? '✅' : '⚠️'}
                    </span>
                    <div>
                        <p className="font-medium capitalize">{sendStatus.method?.replace(/_/g, ' ')}</p>
                        <p className="text-[10px] opacity-70">{sendStatus.details}</p>
                    </div>
                </div>
            )}
        </div>
    )
}
/** Live progress bar with step tracking */
function ProgressBar({ progress, liveSteps }) {
    const { step, totalSteps, message, signalCategory, signalCurrent, signalTotal } = progress || {}
    const stepWeights = [0, 50, 80, 100]
    let percentage = 3

    if (step >= 1 && step <= 3) {
        const basePercent = stepWeights[step - 1]
        const nextPercent = stepWeights[step]
        const stepRange = nextPercent - basePercent
        let subProgress = 0.15
        if (step === 1 && signalCurrent && signalTotal) {
            subProgress = signalCurrent / signalTotal
        }
        const stepComplete = liveSteps.some(s => s.step === step)
        percentage = stepComplete ? nextPercent : basePercent + (stepRange * subProgress)
    }

    return (
        <div className="glass-card rounded-2xl p-5 border border-orange-500/20 animate-slide-up">
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="spinner-fire" style={{ width: '14px', height: '14px', borderWidth: '2px' }} />
                    <p className="text-sm font-medium text-white">{message}</p>
                </div>
                <span className="text-xs text-gray-500 font-mono">{Math.round(percentage)}%</span>
            </div>

            {/* Main progress bar */}
            <div className="h-2 bg-gray-800 rounded-full overflow-hidden mb-4">
                <div
                    className="h-full rounded-full progress-bar-glow"
                    style={{
                        width: `${percentage}%`,
                        background: 'linear-gradient(90deg, #f97316, #ea580c, #f97316)',
                        backgroundSize: '200% 100%',
                        animation: 'progress-shimmer 2s ease-in-out infinite',
                        transition: 'width 0.7s ease-out',
                    }}
                />
            </div>

            {/* Step indicators */}
            <div className="flex items-center justify-between gap-2">
                {PIPELINE_TOOLS.map((tool, i) => {
                    const stepNum = i + 1
                    const isComplete = liveSteps.some(s => s.tool === tool.key && s.status === 'completed')
                    const isError = liveSteps.some(s => s.tool === tool.key && s.status === 'error')
                    const isCurrent = step === stepNum && !isComplete
                    const colors = STEP_COLORS[tool.color]
                    return (
                        <div key={tool.key} className="flex items-center gap-1.5">
                            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                                isError ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                                isComplete ? `${colors.bg} ${colors.text} border ${colors.border}` :
                                isCurrent ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30 animate-pulse' :
                                'bg-gray-800 text-gray-600 border border-gray-700/30'
                            }`}>
                                {isError ? '✗' : isComplete ? '✓' : stepNum}
                            </div>
                            <p className={`text-[10px] font-semibold hidden sm:block ${
                                isError ? 'text-red-400' :
                                isComplete ? colors.text :
                                isCurrent ? 'text-orange-400' :
                                'text-gray-600'
                            }`}>{tool.label}</p>
                            {i < PIPELINE_TOOLS.length - 1 && (
                                <div className={`w-6 h-0.5 hidden sm:block ${isComplete ? colors.dot : 'bg-gray-800'}`} />
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Signal harvesting sub-progress */}
            {step === 1 && signalCategory && (
                <div className="mt-3 flex items-center gap-2 px-1">
                    <span className="text-sm">{CAT_ICONS[signalCategory] || '📌'}</span>
                    <span className="text-[10px] text-gray-400">Scanning</span>
                    <span className="text-[10px] text-blue-400 font-semibold">{signalCategory.replace(/_/g, ' ')}</span>
                    <div className="flex-1 h-1 bg-gray-800 rounded-full overflow-hidden ml-2">
                        <div className="h-full bg-blue-500/50 rounded-full" style={{ width: `${(signalCurrent / signalTotal) * 100}%`, transition: 'width 0.5s ease-out' }} />
                    </div>
                    <span className="text-[10px] text-gray-600 font-mono ml-1">{signalCurrent}/{signalTotal}</span>
                </div>
            )}
        </div>
    )
}
// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────
export default function App() {
    const [icp, setIcp] = useState('We sell high-end cybersecurity training to Series B startups.')
    const [company, setCompany] = useState('Wiz')
    const [email, setEmail] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [result, setResult] = useState(null)
    const [progress, setProgress] = useState(null)
    const [liveSteps, setLiveSteps] = useState([])

    function handleSSEEvent(event) {
        switch (event.type) {
            case 'step_start':
                setProgress({
                    step: event.step,
                    totalSteps: event.total_steps,
                    tool: event.tool,
                    message: event.message,
                    signalCategory: null,
                    signalCurrent: 0,
                    signalTotal: 8,
                })
                break
            case 'signal_category':
                setProgress(p => p ? { ...p, signalCategory: event.category, signalCurrent: event.current, signalTotal: event.total } : p)
                break
            case 'step_done':
                setLiveSteps(prev => [...prev, { step: event.step, tool: event.tool, result: event.result, status: 'completed' }])
                break
            case 'step_error':
                setLiveSteps(prev => [...prev, { step: event.step, tool: event.tool, result: { error: event.error }, status: 'error' }])
                break
            case 'complete':
                setResult(event.result)
                setProgress(null)
                break
        }
    }

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setResult(null)
        setProgress({ step: 0, totalSteps: 3, tool: '', message: 'Initializing agent…', signalCategory: null, signalCurrent: 0, signalTotal: 8 })
        setLiveSteps([])

        const payload = { icp, company, recipient_email: email }
        console.log('[FireReach] 🚀 Sending streaming request:', payload)

        try {
            const res = await fetch(`${API_URL}/api/outreach/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })

            if (!res.ok) {
                const text = await res.text()
                let detail
                try {
                    const body = JSON.parse(text)
                    detail = body.detail || JSON.stringify(body)
                } catch {
                    detail = text || `HTTP ${res.status} ${res.statusText}`
                }
                throw new Error(detail)
            }

            const reader = res.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop() || ''

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue
                    try {
                        const event = JSON.parse(line.slice(6))
                        console.log('[FireReach] SSE event:', event.type, event)
                        handleSSEEvent(event)
                    } catch (parseErr) {
                        console.warn('[FireReach] SSE parse error:', parseErr)
                    }
                }
            }

            if (buffer.startsWith('data: ')) {
                try {
                    handleSSEEvent(JSON.parse(buffer.slice(6)))
                } catch { /* ignore */ }
            }
        } catch (err) {
            const msg = err.message || 'Unknown error'
            const isNetworkError = err.name === 'TypeError' && msg.includes('fetch')
            console.error('[FireReach] ❌ Request failed:', err)

            if (isNetworkError) {
                setError(`Network error — backend not reachable at ${API_URL || 'localhost'}. Is the server running on port 8000?`)
            } else {
                setError(msg)
            }
        } finally {
            setLoading(false)
            setProgress(null)
        }
    }

    const steps = result?.steps || []
    const signalStep = getStepForTool(steps, 'tool_signal_harvester')
    const researchStep = getStepForTool(steps, 'tool_research_analyst')
    const emailStep = getStepForTool(steps, 'tool_outreach_automated_sender')

    return (
        <div className="min-h-screen p-4 lg:p-6">
            {/* ── Page Header ─────────────────────────────────────── */}
            <div className="max-w-6xl mx-auto mb-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                            style={{ background: 'linear-gradient(135deg, #f97316, #dc2626)' }}>
                            🔥
                        </div>
                        <div>
                            <h1 className="text-xl font-black text-white tracking-tight">
                                Fire<span className="text-fire">Reach</span>
                            </h1>
                            <p className="text-xs text-gray-500">Autonomous Outreach Engine</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="badge-online">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                            Online
                        </span>
                        <span className="text-xs text-gray-600 font-mono">v1.0.0</span>
                    </div>
                </div>
            </div>

            <div className="max-w-6xl mx-auto space-y-6">

                {/* ── Form + Pipeline Row ──────────────────────────── */}
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

                    {/* Form Card — 3 cols */}
                    <div className="lg:col-span-3 glass-card rounded-2xl p-6">
                        <div className="mb-5">
                            <h2 className="text-base font-bold text-white mb-1">Configure Outreach</h2>
                            <p className="text-xs text-gray-500">Fill in your target — the agent handles everything else.</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                                    Ideal Customer Profile (ICP)
                                </label>
                                <textarea
                                    className="input-dark resize-none"
                                    rows={2}
                                    value={icp}
                                    onChange={e => setIcp(e.target.value)}
                                    placeholder="Describe who you sell to and what you offer…"
                                    required
                                />
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-400 mb-1.5">Target Company</label>
                                    <input type="text" className="input-dark" value={company}
                                        onChange={e => setCompany(e.target.value)} placeholder="e.g. Wiz, Stripe…" required />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-400 mb-1.5">Recipient Email</label>
                                    <input type="email" className="input-dark" value={email}
                                        onChange={e => setEmail(e.target.value)} placeholder="ciso@company.com" required />
                                </div>
                            </div>
                            <button type="submit" disabled={loading} className="btn-fire w-full text-sm py-3">
                                {loading ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <span className="spinner-fire" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
                                        Agent Running…
                                    </span>
                                ) : '🚀 Launch Outreach Agent'}
                            </button>
                            {loading && !progress && (
                                <p className="text-center text-xs text-gray-500 animate-pulse">
                                    Connecting to agent…
                                </p>
                            )}
                        </form>

                        {error && (
                            <div className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/25 text-sm text-red-300">
                                <p className="font-medium mb-0.5">⚠️ Error</p>
                                <p className="text-xs text-red-400/80 whitespace-pre-wrap break-words">{error}</p>
                                <p className="text-[10px] text-red-400/40 mt-2 font-mono">Check browser console (F12) for full details</p>
                            </div>
                        )}
                    </div>

                    {/* Pipeline + Summary — 2 cols */}
                    <div className="lg:col-span-2 flex flex-col gap-4">
                        <div className="glass-card rounded-2xl p-5 flex-1">
                            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                                Agent Pipeline
                            </h3>
                            <div className="space-y-2">
                                {PIPELINE_TOOLS.map((tool, i) => (
                                    <div key={tool.key} className="flex items-center gap-2">
                                        <PipelineStep tool={tool} status={getStatusBadge(steps, tool.key, steps, liveSteps, progress)} />
                                        {i < PIPELINE_TOOLS.length - 1 && (
                                            <div className="flex-shrink-0 self-center text-gray-700 text-xs">↓</div>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {result && (
                                <div className="mt-4 pt-3 border-t border-gray-700/30">
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono ${result.mode === 'function_calling' ? 'bg-green-500/20 text-green-300' :
                                            result.mode === 'sequential_fallback' ? 'bg-yellow-500/20 text-yellow-300' :
                                                'bg-gray-500/20 text-gray-300'
                                            }`}>
                                            {result.mode === 'function_calling' ? '🤖 AI Agent' :
                                                result.mode === 'sequential_fallback' ? '⚡ Sequential' : result.mode}
                                        </span>
                                        <span className="text-[10px] text-gray-500">{result.total_steps} steps</span>
                                    </div>
                                </div>
                            )}
                        </div>

                    </div>
                </div>

                {/* ── Progress Bar (shown during streaming) ── */}
                {loading && progress && <ProgressBar progress={progress} liveSteps={liveSteps} />}

                {/* ── Output Section (full width below both columns) ── */}
                {result ? (
                    <div className="space-y-5 animate-fade-in">
                        {result.summary && (
                            <div className="glass-card rounded-2xl p-4">
                                <p className="text-xs text-gray-300 leading-relaxed">
                                    <span className="text-orange-400 font-medium">🤖 Summary: </span>
                                    {result.summary}
                                </p>
                            </div>
                        )}

                        {/* Email goes first — it's the main output */}
                        <EmailSection step={emailStep} />

                        {/* Research Brief */}
                        <ResearchSection step={researchStep} />

                        {/* Signals Grid */}
                        <SignalSection step={signalStep} />
                    </div>
                ) : (
                    <div className="glass-card rounded-2xl p-8 flex flex-col items-center justify-center text-center">
                        <div className="text-4xl mb-3 opacity-20">🔥</div>
                        <p className="text-gray-500 text-xs">Results will appear here</p>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="max-w-6xl mx-auto mt-8 text-center">
                <p className="text-xs text-gray-700">
                    FireReach · Powered by <span className="text-orange-500/60">FireReach</span> × <span className="text-blue-400/60">Google Gemini</span>
                </p>
            </div>
        </div>
    )
}
