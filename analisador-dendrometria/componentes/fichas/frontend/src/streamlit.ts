// Protocolo mínimo de componentes do Streamlit (v1), sem a biblioteca oficial,
// que traria uma segunda cópia do React.
type Args = Record<string, unknown>
type Listener = (args: Args) => void

const send = (type: string, data: Record<string, unknown> = {}) =>
  window.parent.postMessage({ isStreamlitMessage: true, type, ...data }, "*")

export const Streamlit = {
  ready: () => send("streamlit:componentReady", { apiVersion: 1 }),
  setFrameHeight: (height: number) => send("streamlit:setFrameHeight", { height }),
  onRender(listener: Listener) {
    const handler = (event: MessageEvent) => {
      const d = event.data as { type?: string; args?: Args } | null
      if (d && d.type === "streamlit:render") listener(d.args ?? {})
    }
    window.addEventListener("message", handler)
    return () => window.removeEventListener("message", handler)
  },
}

/** Mantém a altura do iframe igual à do conteúdo (inclusive ao abrir "Fórmula e notas"). */
export function autoHeight() {
  let last = -1
  const update = () => {
    const h = Math.ceil(document.documentElement.getBoundingClientRect().height)
    if (h !== last) {
      last = h
      Streamlit.setFrameHeight(h)
    }
  }
  new ResizeObserver(update).observe(document.body)
  update()
}
