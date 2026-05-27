import { useState } from 'react'

export default function App() {
  const [count, setCount] = useState(0)

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: '2rem', maxWidth: 720, margin: '0 auto' }}>
      <h1>🤖 AI-Pilot React Demo</h1>
      <p>Claude Code 기반 PoC 교육 환경입니다.</p>
      <button onClick={() => setCount((c) => c + 1)} style={{ padding: '0.5rem 1rem', fontSize: '1rem' }}>
        클릭 횟수: {count}
      </button>
      <p style={{ marginTop: '1rem', color: '#666' }}>
        <code>src/App.jsx</code> 파일을 Claude Code로 수정하며 실습해보세요.
      </p>
    </main>
  )
}
