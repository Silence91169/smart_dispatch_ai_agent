import StatusDot from './StatusDot'

export default function TopBar() {
  return (
    <div className="flex items-center px-4 py-2 bg-slate-900 border-b border-slate-700">
      <span className="text-base font-bold text-slate-100">🚨 Smart Dispatch · Delhi 112</span>
      <div className="ml-auto flex items-center gap-2">
        <StatusDot />
      </div>
    </div>
  )
}
