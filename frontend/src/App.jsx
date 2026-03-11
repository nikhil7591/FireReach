import { useState } from 'react'

// ─── API URL ────────────────────────────────────────────────────────────────
// Uses VITE_API_URL env var in production, falls back to empty (Vite proxy) in dev
const API_URL = import.meta.env.VITE_API_URL || ''

// ─── CONSTANTS ───────────────────────────────────────────────────────────────
const PIPELINE_TOOLS = [
    {
        key: 'tool_signal_harvester',
        icon: '📡',
        label: 'Signal Harvester',
        desc: 'Grounded Google Search',
        color: 'blue',
    },
    {
        key: 'tool_research_analyst',
        icon: '🔬',
        label: 'Research Analyst',
        desc: 'AI Account Brief',
        color: 'purple',
    },
    {
        key: 'tool_outreach_automated_sender',
        icon: '📧',
        label: 'Outreach Sender',
        desc: 'Email Write & Send',
        color: 'green',
    },
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

function getStatusBadge(step, toolKey, steps) {
    if (!steps || steps.length === 0) return 'pending'
    const found = getStepForTool(steps, toolKey)
    if (!found) return 'pending'
    return found.status === 'completed' ? 'done' : 'error'
}

// ─── SUB-COMPONENTS ──────────────────────────────────────────────────────────

/** Spinner shown while agent is running */
function Spinner() {
    return (
        <div className="flex items-center gap-3">
            <div className="spinner-fire" />
            <span className="text-orange-400 font-medium text-sm animate-pulse">Agent Running…</span>
        </div>
    )
}

/** Single pipeline step card */
function PipelineStep({ tool, status, index }) {
    const colors = STEP_COLORS[tool.color]
    const isActive = status === 'done'
    const isError = status === 'error'

    return (
        <div className={`relative flex-1 rounded-xl border p-3 transition-all duration-500 ${isError ? 'bg-red-500/10 border-red-500/30' :
            isActive ? `${colors.bg} ${colors.border}` :
                'bg-gray-900/50 border-gray-700/30'
            }`}>
            <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">{tool.icon}</span>
                <div className="flex-1 min-w-0">
                    <p className={`text-xs font-semibold truncate ${isError ? 'text-red-400' : isActive ? colors.text : 'text-gray-400'
                        }`}>{tool.label}</p>
                    <p className="text-[10px] text-gray-500 truncate">{tool.desc}</p>
                </div>
                {/* Status indicator */}
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${isError ? 'bg-red-400' :
                    isActive ? `${colors.dot} shadow-lg` :
                        'bg-gray-600'
                    } ${isActive ? 'animate-pulse' : ''}`} />
            </div>
            <div className={`text-[10px] font-mono px-1.5 py-0.5 rounded inline-block ${isError ? 'bg-red-500/20 text-red-300' :
                isActive ? 'bg-gray-900/60 text-gray-300' :
                    'bg-gray-800/40 text-gray-500'
                }`}>
                {isError ? 'error' : isActive ? 'done' : 'pending'}
            </div>
        </div>
    )
}

/** Renders the Signal Harvester step detail */
function SignalDetail({ step }) {
    const signals = step?.result?.signals || {}
    const entries = Object.entries(signals).filter(([, v]) => v?.length > 0)
    if (!entries.length) return <p className="text-gray-500 text-sm">No signals captured.</p>

    const catColors = {
        funding: 'text-yellow-400',
        hiring: 'text-blue-400',
        leadership: 'text-purple-400',
        news: 'text-green-400',
        tech_stack: 'text-cyan-400',
        g2_reviews: 'text-pink-400',
        social_mentions: 'text-sky-400',
        competitor_churn: 'text-orange-400',
    }
    const catIcons = {
        funding: '💰',
        hiring: '👥',
        leadership: '👔',
        news: '📰',
        tech_stack: '⚙️',
        g2_reviews: '⭐',
        social_mentions: '📣',
        competitor_churn: '🔄',
    }

    return (
        <div className="space-y-3">
            <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${step?.result?.mode === 'grounded_search' ? 'bg-green-500/20 text-green-300' : 'bg-yellow-500/20 text-yellow-300'}`}>
                    {step?.result?.mode === 'grounded_search' ? '🌐 Live Grounded Search' : '🎭 Demo Mode'}
                </span>
                {step?.result?.sources_count > 0 && (
                    <span className="text-xs text-gray-500">{step.result.sources_count} sources</span>
                )}
            </div>
            {entries.map(([cat, findings]) => (
                <div key={cat}>
                    <p className={`text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-1.5 ${catColors[cat] || 'text-gray-400'}`}>
                        <span>{catIcons[cat] || '📌'}</span>{cat.replace(/_/g, ' ')}
                    </p>
                    {findings.slice(0, 2).map((f, i) => (
                        <div key={i} className="flex gap-2 mb-1">
                            <span className="text-gray-600 mt-0.5">•</span>
                            <div>
                                <p className="text-xs text-gray-300 leading-relaxed">{f.finding}</p>
                                {f.source_url && (
                                    <a href={f.source_url} target="_blank" rel="noreferrer"
                                        className="text-[10px] text-orange-400/60 hover:text-orange-400 truncate block max-w-xs">
                                        {f.source_title || f.source_url}
                                    </a>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    )
}

/** Renders the Research Analyst step detail */
function ResearchDetail({ step }) {
    const res = step?.result || {}
    return (
        <div className="space-y-3">
            {res.account_brief && (
                <div>
                    <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">Account Brief</p>
                    <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-line">{res.account_brief}</p>
                </div>
            )}
            {res.key_signals_identified?.length > 0 && (
                <div>
                    <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">Key Signals</p>
                    <ul className="space-y-1">
                        {res.key_signals_identified.map((s, i) => (
                            <li key={i} className="flex gap-2 text-xs text-gray-300"><span className="text-purple-400">→</span>{s}</li>
                        ))}
                    </ul>
                </div>
            )}
            {res.recommended_angle && (
                <div>
                    <p className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-1">Recommended Angle</p>
                    <p className="text-xs text-gray-200 italic border-l-2 border-purple-500/40 pl-3">{res.recommended_angle}</p>
                </div>
            )}
        </div>
    )
}

/** Renders the Outreach Sender step detail */
function OutreachDetail({ step }) {
    const res = step?.result || {}
    const email = res.email || {}
    const sendStatus = res.send_status || {}
    return (
        <div className="space-y-3">
            {email.subject && (
                <div>
                    <p className="text-xs font-semibold text-green-400 uppercase tracking-wider mb-1">Subject</p>
                    <p className="text-sm font-medium text-orange-300">{email.subject}</p>
                </div>
            )}
            {email.body && (
                <div>
                    <p className="text-xs font-semibold text-green-400 uppercase tracking-wider mb-1">Email Body</p>
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap leading-relaxed font-sans">{email.body}</pre>
                </div>
            )}
            {sendStatus.method && (
                <div className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg ${sendStatus.success ? 'bg-green-500/10 text-green-300 border border-green-500/20' :
                    'bg-yellow-500/10 text-yellow-300 border border-yellow-500/20'
                    }`}>
                    <span>{sendStatus.success ? '✓' : '⚠'}</span>
                    <span className="font-medium capitalize">{sendStatus.method?.replace('_', ' ')}</span>
                    <span className="text-gray-400">— {sendStatus.details}</span>
                </div>
            )}
        </div>
    )
}

/** The big generated email showcase card */
function EmailShowcase({ steps }) {
    const senderStep = getStepForTool(steps, 'tool_outreach_automated_sender')
    const email = senderStep?.result?.email
    const sendStatus = senderStep?.result?.send_status
    if (!email?.subject) return null

    return (
        <div className="glass-card rounded-2xl p-6 animate-slide-up">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <span>📧</span> Generated Email
            </h3>
            {/* Subject */}
            <div className="mb-4 p-3 rounded-xl bg-orange-500/8 border border-orange-500/20">
                <p className="text-[10px] font-mono text-gray-500 mb-1">SUBJECT</p>
                <p className="text-sm font-semibold text-orange-300">{email.subject}</p>
            </div>
            {/* Body */}
            <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-700/30 mb-4">
                <pre className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed font-sans">{email.body}</pre>
            </div>
            {/* Send Status */}
            {sendStatus && (
                <div className={`flex items-center gap-3 p-3 rounded-xl text-sm ${sendStatus.method === 'preview_only' ? 'bg-blue-500/10 border border-blue-500/20 text-blue-300' :
                    sendStatus.success ? 'bg-green-500/10 border border-green-500/20 text-green-300' :
                        'bg-yellow-500/10 border border-yellow-500/20 text-yellow-300'
                    }`}>
                    <span className="text-lg">
                        {sendStatus.method === 'preview_only' ? '👁️' : sendStatus.success ? '✅' : '⚠️'}
                    </span>
                    <div>
                        <p className="font-medium capitalize">{sendStatus.method?.replace(/_/g, ' ')}</p>
                        <p className="text-xs opacity-70">{sendStatus.details}</p>
                    </div>
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

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        setError(null)
        setResult(null)

        try {
            const res = await fetch(`${API_URL}/api/outreach`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ icp, company, recipient_email: email }),
            })

            if (!res.ok) {
                const body = await res.json().catch(() => ({}))
                throw new Error(body.detail || `HTTP ${res.status}`)
            }

            const data = await res.json()
            setResult(data)
        } catch (err) {
            setError(err.message || 'Something went wrong. Check backend is running.')
        } finally {
            setLoading(false)
        }
    }

    const steps = result?.steps || []

    return (
        <div className="min-h-screen p-4 lg:p-6">
            {/* ── Page Header ─────────────────────────────────────── */}
            <div className="max-w-7xl mx-auto mb-6">
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

            {/* ── Two-Column Layout ────────────────────────────────── */}
            <div className="max-w-7xl mx-auto grid grid-cols-1 xl:grid-cols-2 gap-6">

                {/* ══ LEFT COLUMN ══════════════════════════════════════ */}
                <div className="space-y-5">

                    {/* Form Card */}
                    <div className="glass-card rounded-2xl p-6">
                        <div className="mb-5">
                            <h2 className="text-base font-bold text-white mb-1">Configure Outreach</h2>
                            <p className="text-xs text-gray-500">Fill in your target — the agent handles everything else.</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            {/* ICP */}
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                                    Ideal Customer Profile (ICP)
                                </label>
                                <textarea
                                    className="input-dark resize-none"
                                    rows={3}
                                    value={icp}
                                    onChange={e => setIcp(e.target.value)}
                                    placeholder="Describe who you sell to and what you offer…"
                                    required
                                />
                            </div>

                            {/* Company */}
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                                    Target Company
                                </label>
                                <input
                                    type="text"
                                    className="input-dark"
                                    value={company}
                                    onChange={e => setCompany(e.target.value)}
                                    placeholder="e.g. Wiz, Stripe, Figma…"
                                    required
                                />
                            </div>

                            {/* Email */}
                            <div>
                                <label className="block text-xs font-medium text-gray-400 mb-1.5">
                                    Recipient Email
                                </label>
                                <input
                                    type="email"
                                    className="input-dark"
                                    value={email}
                                    onChange={e => setEmail(e.target.value)}
                                    placeholder="ciso@targetcompany.com"
                                    required
                                />
                            </div>

                            {/* Submit */}
                            <button type="submit" disabled={loading} className="btn-fire w-full text-sm py-3">
                                {loading ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <span className="spinner-fire w-4 h-4 border-2" style={{ width: '16px', height: '16px' }} />
                                        Agent Running…
                                    </span>
                                ) : '🚀 Launch Outreach Agent'}
                            </button>

                            {/* Loading state message */}
                            {loading && (
                                <p className="text-center text-xs text-gray-500 animate-pulse">
                                    Harvesting signals · Analyzing · Writing email…
                                </p>
                            )}
                        </form>

                        {/* Error */}
                        {error && (
                            <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/25 text-sm text-red-300">
                                <p className="font-medium mb-0.5">⚠️ Error</p>
                                <p className="text-xs text-red-400/80">{error}</p>
                            </div>
                        )}
                    </div>

                    {/* Pipeline Visualization */}
                    <div className="glass-card rounded-2xl p-5">
                        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
                            Agent Pipeline
                        </h3>
                        <div className="flex gap-2 items-center">
                            {PIPELINE_TOOLS.map((tool, i) => (
                                <div key={tool.key} className="flex items-center flex-1 gap-2">
                                    <PipelineStep
                                        tool={tool}
                                        status={getStatusBadge(steps, tool.key, steps)}
                                        index={i}
                                    />
                                    {i < PIPELINE_TOOLS.length - 1 && (
                                        <div className="flex-shrink-0">
                                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                                <path d="M3 7h8M8 4l3 3-3 3" stroke="#374151" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                            </svg>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Result summary */}
                        {result?.summary && (
                            <div className="mt-4 p-3 rounded-xl bg-orange-500/5 border border-orange-500/15 text-xs text-gray-300 leading-relaxed">
                                <span className="text-orange-400 font-medium">🤖 Summary: </span>
                                {result.summary}
                            </div>
                        )}
                    </div>

                    {/* Step details — only on mobile or when no right column needed */}
                    {result && (
                        <div className="xl:hidden space-y-4 animate-fade-in">
                            <EmailShowcase steps={steps} />
                            <StepCards steps={steps} />
                        </div>
                    )}
                </div>

                {/* ══ RIGHT COLUMN ═════════════════════════════════════ */}
                {result && (
                    <div className="hidden xl:flex flex-col gap-5 animate-fade-in">
                        <EmailShowcase steps={steps} />
                        <StepCards steps={steps} />
                    </div>
                )}

                {/* Empty right column placeholder when no result */}
                {!result && (
                    <div className="hidden xl:flex flex-col items-center justify-center glass-card rounded-2xl p-12 text-center">
                        <div className="text-5xl mb-4 opacity-30">🔥</div>
                        <p className="text-gray-500 text-sm font-medium">Results will appear here</p>
                        <p className="text-gray-600 text-xs mt-1">Configure your outreach and launch the agent</p>
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="max-w-7xl mx-auto mt-8 text-center">
                <p className="text-xs text-gray-700">
                    FireReach · Powered by <span className="text-orange-500/60">FireReach</span> × <span className="text-blue-400/60">Google Gemini 2.0 Flash</span>
                </p>
            </div>
        </div>
    )
}

// ─── STEP CARDS COMPONENT ─────────────────────────────────────────────────────
function StepCards({ steps }) {
    if (!steps?.length) return null

    return (
        <div className="space-y-4">
            {PIPELINE_TOOLS.map((tool) => {
                const step = getStepForTool(steps, tool.key)
                if (!step) return null
                const colors = STEP_COLORS[tool.color]

                return (
                    <div key={tool.key} className={`glass-card rounded-2xl p-5 border ${colors.border} animate-slide-up`}>
                        <div className="flex items-center gap-2 mb-4">
                            <span className="text-xl">{tool.icon}</span>
                            <div>
                                <h3 className={`text-sm font-bold ${colors.text}`}>{tool.label}</h3>
                                <p className="text-[10px] text-gray-500 font-mono">{tool.key}</p>
                            </div>
                            <div className={`ml-auto text-[10px] px-2 py-0.5 rounded-full font-medium ${step.status === 'completed' ? `${colors.bg} ${colors.text}` : 'bg-red-500/10 text-red-400'
                                }`}>
                                {step.status}
                            </div>
                        </div>

                        {/* Render the right detail component */}
                        {tool.key === 'tool_signal_harvester' && <SignalDetail step={step} />}
                        {tool.key === 'tool_research_analyst' && <ResearchDetail step={step} />}
                        {tool.key === 'tool_outreach_automated_sender' && <OutreachDetail step={step} />}
                    </div>
                )
            })}
        </div>
    )
}
