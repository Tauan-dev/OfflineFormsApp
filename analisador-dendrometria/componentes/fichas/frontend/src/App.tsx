import { Fragment, useEffect, useId, useRef, useState } from "react"
import { MotionConfig, motion, useReducedMotion } from "motion/react"
import { Streamlit, autoHeight } from "./streamlit"
import { BlurFade } from "./components/blur-fade"
import CountUp from "./components/CountUp"
import SpotlightCard from "./components/SpotlightCard"
import { cn } from "./lib/utils"

/** Uma ficha de indicador, já formatada pelo Python (a interface não calcula nada). */
type Ficha = {
  chave: string
  titulo: string
  valor_txt: string          // texto final exibido, no padrão brasileiro
  alvo: number | null        // número para a contagem animada (null = sem animação)
  casas: number
  unidade: string
  classe: "ok" | "warn" | "err" | "blk"
  rotulo: string             // "✓ cálculo válido", "! cálculo com ressalva"…
  estado: string             // rótulo sem ícone, para leitores de tela
  sem_valor: boolean
  denominador: string
  cobertura: number | null   // 0–100; null = sem barra
  barra: boolean             // reservar o espaço da barra (mantém alinhamento)
  ressalva: string
  formula: string
  notas: string[]
  filtrado: boolean
}

const COR: Record<Ficha["classe"], { topo: string; luz: string; texto: string; barra: string }> = {
  ok: { topo: "bg-ok", luz: "#1E7A4F", texto: "text-ok-t", barra: "bg-ok" },
  warn: { topo: "bg-warn", luz: "#C58B1A", texto: "text-warn-t", barra: "bg-warn" },
  err: { topo: "bg-err", luz: "#B3261E", texto: "text-err", barra: "bg-err" },
  blk: { topo: "bg-blk", luz: "#6B7780", texto: "text-blk-t", barra: "bg-blk" },
}

type CartaoProps = {
  f: Ficha
  ordem: number
  aberto: boolean
  painelId: string
  onNotas: () => void
  botaoRef: (el: HTMLButtonElement | null) => void
}

function Cartao({ f, ordem, aberto, painelId, onNotas, botaoRef }: CartaoProps) {
  const id = useId()
  const calmo = useReducedMotion()
  const cor = COR[f.classe] ?? COR.blk
  return (
    <SpotlightCard
      theme="light"
      spotlightColor={cor.luz}
      intensity={0.35}
      spotlightSize={220}
      borderGlow={0.5}
      flare={false}
      aria-labelledby={`${id}-t`}
      role="group"
      className={cn(
        "flex h-full flex-col rounded-[2px] px-[13px] pt-[13px] pb-[10px]",
        "transition-transform duration-300 hover:-translate-y-0.5 focus-within:-translate-y-0.5",
        "motion-reduce:transition-none motion-reduce:hover:translate-y-0 motion-reduce:focus-within:translate-y-0",
        f.classe === "blk" && "hachura",
        aberto && "ring-2 ring-marca ring-offset-1"
      )}
    >
      <span aria-hidden className={cn("absolute inset-x-0 top-0 h-[3px]", cor.topo)} />
      <div id={`${id}-t`} className="min-h-[2.5em] text-[.85rem] leading-[1.25] font-semibold text-sub">
        {f.titulo}
        <span className="sr-only">: {f.sem_valor ? "sem valor calculado" : `${f.valor_txt} ${f.unidade}`}, {f.estado}</span>
      </div>

      {f.sem_valor ? (
        <div className="pt-1 pb-0.5 text-[.98rem] leading-[1.3] font-bold text-blk-t">Sem valor calculado</div>
      ) : (
        <div aria-hidden className="mt-0.5 font-serif text-[1.9rem] leading-[1.15] font-semibold [font-variant-numeric:lining-nums_tabular-nums]">
          {f.alvo !== null ? (
            <CountUp
              to={f.alvo}
              decimals={f.casas}
              separator="."
              decimalSeparator=","
              mode="roll"
              easing="expo"
              duration={1.1}
              delay={0.08 * ordem}
            />
          ) : (
            f.valor_txt
          )}
          <small className="ml-1 font-sans text-[.85rem] font-normal text-sub">{f.unidade}</small>
        </div>
      )}

      {f.barra && (
        <div className="mt-[9px] mb-[6px] h-1 overflow-hidden rounded-[2px] bg-[#E3E9E3]" style={f.cobertura === null ? { background: "transparent" } : undefined}>
          {f.cobertura !== null && (
            <motion.div
              role="img"
              aria-label={`cobertura ${f.cobertura.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`}
              className={cn("h-full origin-left", cor.barra)}
              style={{ width: `${f.cobertura}%` }}
              initial={{ scaleX: calmo ? 1 : 0 }}
              whileInView={{ scaleX: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.9, ease: [0.2, 0.7, 0.2, 1], delay: 0.15 + 0.08 * ordem }}
            />
          )}
        </div>
      )}

      <div className="min-h-[4em] text-[.8rem] leading-[1.35] text-sub">{f.denominador}</div>

      {f.ressalva && (
        <p className="mt-2 mb-0 rounded-r-[2px] border-l-[3px] border-warn bg-[#FBF3D9] px-[9px] py-[7px] text-[.8rem] leading-[1.4] text-[#4A3700]">
          <b className="text-warn-t">Ressalva:</b> {f.ressalva}
        </p>
      )}

      <div className="mt-auto pt-2">
        <div className={cn("text-[.8rem] font-bold", cor.texto)} aria-hidden>
          {f.rotulo}
          {f.filtrado && (
            <em className="ml-2 rounded-[2px] border border-marca px-[5px] text-[.74rem] font-semibold text-marca not-italic">
              filtrado
            </em>
          )}
        </div>
        {(f.formula || f.notas.length > 0) && (
          <button
            ref={botaoRef}
            type="button"
            onClick={onNotas}
            aria-expanded={aberto}
            aria-controls={painelId}
            className={cn(
              "mt-1.5 inline-flex min-h-7 cursor-pointer items-center gap-1.5 rounded-[2px] border px-2 py-0.5",
              "text-[.78rem] font-semibold transition-colors",
              aberto ? "border-marca bg-marca text-white" : "border-rule bg-white text-marca hover:border-marca"
            )}
          >
            <span aria-hidden className={cn("inline-block transition-transform motion-reduce:transition-none", aberto && "rotate-90")}>▸</span>
            Fórmula e notas{f.notas.length > 0 ? ` (${f.notas.length + (f.formula ? 1 : 0)})` : ""}
          </button>
        )}
      </div>
    </SpotlightCard>
  )
}

/** Painel de leitura: ocupa a largura da grade, logo abaixo da linha do cartão aberto. */
function Painel({ f, id, onFechar }: { f: Ficha; id: string; onFechar: () => void }) {
  const tituloRef = useRef<HTMLHeadingElement>(null)
  useEffect(() => {
    tituloRef.current?.focus({ preventScroll: true })
    tituloRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" })
  }, [f.chave])
  return (
    <motion.section
      id={id}
      role="region"
      aria-labelledby={`${id}-h`}
      onKeyDown={(e) => e.key === "Escape" && onFechar()}
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className="col-span-full rounded-[2px] border border-rule border-l-4 border-l-marca bg-[#F7FAF6] px-6 py-5"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-[.78rem] font-semibold text-sub">Fórmula e notas</div>
          <h3 id={`${id}-h`} ref={tituloRef} tabIndex={-1} className="m-0 font-serif text-[1.25rem] font-semibold text-marca outline-none">
            {f.titulo}
          </h3>
        </div>
        <button
          type="button"
          onClick={onFechar}
          className="min-h-8 shrink-0 cursor-pointer rounded-[2px] border border-rule bg-white px-3 text-[.85rem] font-semibold text-marca hover:border-marca"
        >
          Fechar <span className="sr-only">fórmula e notas de {f.titulo}</span>
          <span aria-hidden className="ml-1 text-sub">Esc</span>
        </button>
      </div>

      <div className="mt-4 grid gap-6 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <div className="min-w-0">
          {f.formula && (
            <>
              <div className="mb-1 text-[.8rem] font-semibold text-sub">Fórmula</div>
              <p className="m-0 rounded-[2px] border border-rule bg-white px-4 py-3 font-serif text-[1.1rem] leading-[1.5] text-ink break-words">
                {f.formula}
              </p>
            </>
          )}
          <dl className="mt-4 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-[.88rem]">
            <dt className="font-semibold text-sub">Valor</dt>
            <dd className="m-0">{f.sem_valor ? "sem valor calculado" : `${f.valor_txt} ${f.unidade}`}</dd>
            <dt className="font-semibold text-sub">Estado</dt>
            <dd className="m-0">{f.estado}</dd>
            <dt className="font-semibold text-sub">Base</dt>
            <dd className="m-0">{f.denominador}</dd>
          </dl>
        </div>
        <div className="min-w-0">
          {f.ressalva && (
            <p className="mt-0 mb-3 max-w-[72ch] rounded-r-[2px] border-l-[3px] border-warn bg-[#FBF3D9] px-3 py-2 text-[.92rem] leading-[1.55] text-[#4A3700]">
              <b className="text-warn-t">Ressalva:</b> {f.ressalva}
            </p>
          )}
          {f.notas.length > 0 ? (
            <>
              <div className="mb-1 text-[.8rem] font-semibold text-sub">Notas</div>
              <ul className="m-0 max-w-[72ch] list-none space-y-2.5 p-0">
                {f.notas.map((n, i) => (
                  <li key={i} className="border-l-2 border-rule pl-3 text-[.92rem] leading-[1.6] text-ink">{n}</li>
                ))}
              </ul>
            </>
          ) : (
            !f.ressalva && <p className="m-0 text-[.92rem] text-sub">Sem notas adicionais para este indicador.</p>
          )}
        </div>
      </div>
    </motion.section>
  )
}

/** Colunas efetivas: a grade se reduz em telas estreitas. */
function colunasEfetivas(cols: number) {
  const w = window.innerWidth
  return w <= 420 ? 1 : w <= 760 ? Math.min(2, cols) : cols
}

export default function App() {
  const [fichas, setFichas] = useState<Ficha[]>([])
  const [cols, setCols] = useState(4)
  const [efetivas, setEfetivas] = useState(4)
  const [aberto, setAberto] = useState<string | null>(null)
  const botoes = useRef<Record<string, HTMLButtonElement | null>>({})
  const base = useId()
  const calmo = useReducedMotion()

  useEffect(() => {
    const off = Streamlit.onRender((args) => {
      setFichas((args.fichas as Ficha[]) ?? [])
      setCols(Number(args.colunas) || 4)
    })
    Streamlit.ready()
    autoHeight()
    return off
  }, [])

  useEffect(() => {
    const r = () => setEfetivas(colunasEfetivas(cols))
    r()
    window.addEventListener("resize", r)
    return () => window.removeEventListener("resize", r)
  }, [cols])

  useEffect(() => {  // a ficha aberta pode sumir após um filtro
    if (aberto && !fichas.some((f) => f.chave === aberto)) setAberto(null)
  }, [fichas, aberto])

  const fechar = () => {
    const k = aberto
    setAberto(null)
    if (k) requestAnimationFrame(() => botoes.current[k]?.focus())
  }

  const linhas: Ficha[][] = []
  for (let i = 0; i < fichas.length; i += efetivas) linhas.push(fichas.slice(i, i + efetivas))
  const painelId = (k: string) => `${base}-painel-${k}`

  return (
    <MotionConfig reducedMotion="user">
      <div className="grade" style={{ ["--cols" as string]: efetivas }}>
        {linhas.map((linha, li) => (
          <Fragment key={li}>
            {linha.map((f, ci) => {
              const ordem = li * efetivas + ci
              const cartao = (
                <Cartao
                  f={f}
                  ordem={ordem}
                  aberto={aberto === f.chave}
                  painelId={painelId(f.chave)}
                  onNotas={() => setAberto(aberto === f.chave ? null : f.chave)}
                  botaoRef={(el) => { botoes.current[f.chave] = el }}
                />
              )
              return calmo ? (
                <div key={f.chave} className="h-full">{cartao}</div>
              ) : (
                <BlurFade key={f.chave} delay={0.07 * ordem} offset={10} direction="up" blur="5px" className="h-full">
                  {cartao}
                </BlurFade>
              )
            })}
            {linha.some((f) => f.chave === aberto) && (
              <Painel
                key={`painel-${aberto}`}
                f={linha.find((f) => f.chave === aberto)!}
                id={painelId(aberto!)}
                onFechar={fechar}
              />
            )}
          </Fragment>
        ))}
      </div>
    </MotionConfig>
  )
}
