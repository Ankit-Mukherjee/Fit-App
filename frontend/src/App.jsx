import { useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

// Use environment variable if available (build-time), otherwise try window config (runtime), fallback to localhost
const API_BASE = import.meta.env.VITE_API_BASE_URL || 
                 (typeof window !== 'undefined' && window.APP_CONFIG?.API_BASE_URL) ||
                 'http://localhost:8000'

const genderOptions = [
  { label: 'Female', value: 'female' },
  { label: 'Male', value: 'male' },
  { label: 'Non-binary', value: 'non-binary' },
  { label: 'Prefer not to say', value: 'unspecified' },
]

const activityLevels = [
  { label: 'Sedentary', value: 'sedentary', description: 'Little or no exercise' },
  { label: 'Lightly Active', value: 'light', description: '1-3 workouts per week' },
  { label: 'Moderately Active', value: 'moderate', description: '3-5 workouts per week' },
  { label: 'Very Active', value: 'very', description: '6-7 intense workouts per week' },
  { label: 'Athlete', value: 'athlete', description: 'Multiple sessions per day' },
]

const goalOptions = [
  { label: 'Build Muscle', value: 'build muscle' },
  { label: 'Lose Fat', value: 'lose fat' },
  { label: 'Recomposition', value: 'recomposition' },
  { label: 'Improve Performance', value: 'performance' },
]

const macroLabels = {
  calories: { label: 'Calories', suffix: 'kcal' },
  protein: { label: 'Protein', suffix: 'g' },
  carbs: { label: 'Carbs', suffix: 'g' },
  fat: { label: 'Fat', suffix: 'g' },
  fiber: { label: 'Fiber', suffix: 'g' },
  water: { label: 'Water', suffix: 'L' },
}

const normalizeMacroPlan = (text) => {
  if (!text) {
    return { type: 'text', data: '' }
  }

  const trimmed = text.trim()
  if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
    try {
      const parsed = JSON.parse(trimmed)
      if (parsed && typeof parsed === 'object') {
        return { type: 'structured', data: parsed }
      }
    } catch (error) {
      // fall through to text output
    }
  }

  return { type: 'text', data: text }
}

const markdownComponents = {
  h1: ({ node, ...props }) => <h2 className="md-heading" {...props} />,
  h2: ({ node, ...props }) => <h3 className="md-subheading" {...props} />,
  h3: ({ node, ...props }) => <h4 className="md-subheading" {...props} />,
  p: ({ node, ...props }) => <p className="md-body" {...props} />,
  ul: ({ node, ...props }) => <ul className="md-list" {...props} />,
  li: ({ node, ...props }) => <li className="md-list-item" {...props} />,
  strong: ({ node, ...props }) => <strong className="md-strong" {...props} />,
}

function App() {
  const [profile, setProfile] = useState({
    name: '',
    age: '',
    gender: 'male',
    height: '',
    weight: '',
    activity: 'moderate',
    bodyFat: '',
    goal: 'build muscle',
  })

  const [question, setQuestion] = useState('What is a good bicep workout?')
  const [macroPlan, setMacroPlan] = useState(null)
  const [advice, setAdvice] = useState('')
  const [loading, setLoading] = useState({ macros: false, advice: false, notes: false })
  const [error, setError] = useState('')
  const [userId] = useState(() => `user-${Math.random().toString(36).substr(2, 9)}`)

  const profileSummary = useMemo(() => {
    const { age, gender, height, weight, activity, bodyFat } = profile
    return `Age ${age}, ${gender}, ${height} cm, ${weight} kg, body fat ${bodyFat || 'n/a'}%, activity level ${activity}.`
  }, [profile])

  const isProfileComplete = useMemo(() => {
    return profile.age && profile.height && profile.weight
  }, [profile])

  const handleProfileChange = (field, value) => {
    setProfile((prev) => ({ ...prev, [field]: value }))
  }

  const handleGenerateMacros = async () => {
    setError('')
    if (!isProfileComplete) {
      setError('Please complete age, height, and weight to generate macros.')
      return
    }

    setLoading((prev) => ({ ...prev, macros: true }))
    try {
      const response = await fetch(`${API_BASE}/macro-plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal: profile.goal,
          profile,
        }),
      })

      if (!response.ok) {
        throw new Error('Macro plan request failed')
      }

      const data = await response.json()
      const text =
        data.text || data.plan || data.message || JSON.stringify(data, null, 2)
      setMacroPlan(normalizeMacroPlan(text))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading((prev) => ({ ...prev, macros: false }))
    }
  }

  const handleAskCoach = async () => {
    setError('')
    if (!question.trim()) {
      setError('Add a question before asking the coach.')
      return
    }

    setLoading((prev) => ({ ...prev, advice: true }))
    try {
      const response = await fetch(`${API_BASE}/workout-advice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          profileSummary,
          question,
          userId,
        }),
      })

      if (!response.ok) {
        throw new Error('Advice request failed')
      }

      const data = await response.json()
      const text = data.text || data.advice || data.message || JSON.stringify(data, null, 2)
      setAdvice(text)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading((prev) => ({ ...prev, advice: false }))
    }
  }

  const handleSaveMacrosToNotes = async () => {
    if (!macroPlan) return

    setLoading((prev) => ({ ...prev, notes: true }))
    try {
      const macroText = macroPlan.type === 'structured' 
        ? Object.entries(macroPlan.data).map(([k, v]) => `${k}: ${v}`).join(', ')
        : macroPlan.data

      const response = await fetch(`${API_BASE}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          text: `My daily macros: ${macroText}`,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to save macros to notes')
      }

      // Show success message briefly
      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading((prev) => ({ ...prev, notes: false }))
    }
  }

  const handleSaveAdviceToNotes = async () => {
    if (!advice) return

    setLoading((prev) => ({ ...prev, notes: true }))
    try {
      const response = await fetch(`${API_BASE}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          text: `Q: ${question}\nA: ${advice.substring(0, 200)}...`,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to save advice to notes')
      }

      setError('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading((prev) => ({ ...prev, notes: false }))
    }
  }

  return (
    <div className="page">
      <div className="blur blur-one" />
      <div className="blur blur-two" />
      <header className="hero">
        <div className="hero__content">
          <p className="hero__eyebrow">FitFlow Coach</p>
          <h1>Personalized fuel & training guidance, powered by AI.</h1>
          <p className="hero__subhead">
            Enter your training profile and goals to instantly generate custom macro
            recommendations and ask follow-up questions to your virtual coach.
          </p>
        </div>
        <div className="hero__cta">
          <button className="primary" onClick={handleGenerateMacros}>
            Generate My Plan
          </button>
        </div>
      </header>

      <main className="layout">
        <section className="card form-card">
          <h2>Your Training Profile</h2>
          <div className="form">
            <div className="form__row">
              <label>
                Name
                <input
                  type="text"
                  placeholder="Jordan"
                  value={profile.name}
                  onChange={(e) => handleProfileChange('name', e.target.value)}
                />
              </label>
              <label>
                Age
                <input
                  type="number"
                  min="14"
                  max="90"
                  value={profile.age}
                  onChange={(e) => handleProfileChange('age', e.target.value)}
                />
              </label>
              <label>
                Gender
                <select
                  value={profile.gender}
                  onChange={(e) => handleProfileChange('gender', e.target.value)}
                >
                  {genderOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="form__row">
              <label>
                Height (cm)
                <input
                  type="number"
                  min="120"
                  max="230"
                  value={profile.height}
                  onChange={(e) => handleProfileChange('height', e.target.value)}
                />
              </label>
              <label>
                Weight (kg)
                <input
                  type="number"
                  min="40"
                  max="180"
                  value={profile.weight}
                  onChange={(e) => handleProfileChange('weight', e.target.value)}
                />
              </label>
              <label>
                Body Fat %
                <input
                  type="number"
                  min="5"
                  max="50"
                  value={profile.bodyFat}
                  onChange={(e) => handleProfileChange('bodyFat', e.target.value)}
                  placeholder="Optional"
                />
              </label>
            </div>
            <div className="form__row">
              <label>
                Activity Level
                <select
                  value={profile.activity}
                  onChange={(e) => handleProfileChange('activity', e.target.value)}
                >
                  {activityLevels.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Goal
                <select
                  value={profile.goal}
                  onChange={(e) => handleProfileChange('goal', e.target.value)}
                >
                  {goalOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>
          <div className="card__footer">
            <button
              className="primary"
              onClick={handleGenerateMacros}
              disabled={loading.macros}
            >
              {loading.macros ? 'Generating...' : 'Generate Macro Plan'}
            </button>
            <span className="hint">We’ll analyse your inputs before calculating macros.</span>
          </div>
        </section>

        <div className="results-column">
          <section className="card output-card">
            <div className="section-heading">
              <h2>Macro Blueprint</h2>
              <span className="badge">AI Generated</span>
            </div>
            <div className="macro-output">
              {macroPlan ? (
                macroPlan.type === 'structured' ? (
                  <div className="macro-column">
                    {Object.entries(macroPlan.data).map(([key, value]) => {
                      const label = macroLabels[key]?.label ?? key
                      const suffix = macroLabels[key]?.suffix ?? ''
                      return (
                        <div key={key} className="stat-card">
                          <span className="stat-card__label">{label}</span>
                          <span className="stat-card__value">
                            {typeof value === 'number' ? value.toLocaleString() : value}
                            {suffix ? <span className="stat-card__suffix"> {suffix}</span> : null}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <pre>{macroPlan.data}</pre>
                )
              ) : (
                <p className="placeholder">
                  Fill out your profile and tap “Generate Macro Plan” to view your personalised
                  nutrition blueprint.
                </p>
              )}
            </div>
            {macroPlan && (
              <div className="card__footer">
                <button
                  className="secondary"
                  onClick={handleSaveMacrosToNotes}
                  disabled={loading.notes}
                >
                  {loading.notes ? 'Saving...' : '💾 Save to Notes'}
                </button>
              </div>
            )}
          </section>

          <section className="card advice-card">
            <div className="section-heading">
              <h2>Ask the Coach</h2>
              <span className="hint">Use your macro plan as context</span>
            </div>
            <textarea
              rows="4"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask anything about workouts, recovery, or nutrition..."
            />
            <div className="card__footer">
              <button
                className="secondary"
                onClick={handleAskCoach}
                disabled={loading.advice}
              >
                {loading.advice ? 'Thinking...' : 'Get Advice'}
              </button>
            </div>
          </section>

          <section className="advice-section">
            <div className="advice-output">
              {advice ? (
                <article className="advice-article">
                  <ReactMarkdown components={markdownComponents}>{advice}</ReactMarkdown>
                </article>
              ) : (
                <p className="placeholder">The coach's advice will appear here.</p>
              )}
            </div>
            {advice && (
              <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  className="secondary"
                  onClick={handleSaveAdviceToNotes}
                  disabled={loading.notes}
                  style={{ fontSize: '0.9rem', padding: '0.6rem 1.2rem' }}
                >
                  {loading.notes ? 'Saving...' : '💾 Save to Notes'}
                </button>
              </div>
            )}
          </section>
        </div>
      </main>

      {error && <div className="toast error">{error}</div>}
    </div>
  )
}

export default App
