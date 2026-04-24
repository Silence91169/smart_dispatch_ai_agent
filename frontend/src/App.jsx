import { Component } from 'react'
import Dashboard from './components/layout/Dashboard'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }
  static getDerivedStateFromError(error) {
    return { error }
  }
  render() {
    if (this.state.error) {
      return (
        <div className="h-full flex flex-col items-center justify-center bg-slate-950 text-slate-200 gap-4 p-8">
          <span className="text-4xl">💥</span>
          <h1 className="text-lg font-bold text-red-400">Dashboard error</h1>
          <pre className="text-xs text-slate-400 bg-slate-900 p-4 rounded max-w-xl overflow-auto">
            {this.state.error?.message}
          </pre>
          <button
            onClick={() => this.setState({ error: null })}
            className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded"
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  )
}
