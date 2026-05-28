// Renderiza texto Markdown (respuestas de la IA) con formato y resaltado de codigo.
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github-dark.css'

// Bloque de codigo con boton para copiar.
function CodeBlock({ className, children }) {
  const [copied, setCopied] = useState(false)
  const code = String(children).replace(/\n$/, '')

  async function copy() {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* el navegador puede bloquear el portapapeles sin https */
    }
  }

  return (
    <div className="code-wrap">
      <button className="code-copy" onClick={copy}>
        {copied ? '✓ copiado' : 'copiar'}
      </button>
      <pre>
        <code className={className}>{children}</code>
      </pre>
    </div>
  )
}

function Markdown({ children }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // Distinguir codigo en bloque (```...```) de codigo en linea (`x`).
          // react-markdown v10 ya no pasa `inline`, asi que lo deducimos: es bloque
          // si tiene clase de lenguaje (language-...) o contiene saltos de linea.
          code({ className, children, ...props }) {
            const texto = String(children)
            const esBloque = /language-/.test(className || '') || texto.includes('\n')
            if (!esBloque) {
              return (
                <code className="inline-code" {...props}>
                  {children}
                </code>
              )
            }
            return <CodeBlock className={className}>{children}</CodeBlock>
          },
          // Los enlaces se abren en una pestaña nueva.
          a({ children, ...props }) {
            return (
              <a target="_blank" rel="noreferrer" {...props}>
                {children}
              </a>
            )
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  )
}

export default Markdown
