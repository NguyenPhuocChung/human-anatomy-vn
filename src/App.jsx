import React, { Suspense, useMemo, useRef, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, useGLTF, Bounds, Html } from '@react-three/drei'
import * as THREE from 'three'
import { lookup } from './labels.js'
import { SOURCES } from './sources.js'

// Các lớp hệ thống giải phẫu (xuất từ Startup.blend của Z-Anatomy)
const LAYERS = [
  { id: 'skeleton',       url: 'models/skeleton.glb',       zh: 'Hệ xương' },
  { id: 'muscular',       url: 'models/muscular.glb',       zh: 'Hệ cơ' },
  { id: 'cardiovascular', url: 'models/cardiovascular.glb', zh: 'Hệ tim mạch' },
  { id: 'nervous',        url: 'models/nervous.glb',        zh: 'Hệ thần kinh và giác quan' },
  { id: 'visceral',       url: 'models/visceral.glb',       zh: 'Hệ nội tạng' },
]

LAYERS.forEach((l) => useGLTF.preload(l.url, 'draco/'))

const SELECT_COLOR = new THREE.Color('#ff5252')
const HOVER_EMISSIVE = new THREE.Color('#ffd24a')

// Làm nổi bật hover theo kiểu mệnh lệnh: trực tiếp thay đổi phát sáng vật liệu, tránh render lại React từng khung hình.
function setHover(o, on) {
  const m = o && o.material
  if (!m || !m.emissive) return
  if (on) {
    if (m.userData._e === undefined) m.userData._e = m.emissive.getHex()
    m.emissive.copy(HOVER_EMISSIVE)
    m.emissiveIntensity = 0.55
  } else {
    if (m.userData._e !== undefined) m.emissive.setHex(m.userData._e)
    else m.emissive.setHex(0x000000)
    m.emissiveIntensity = 1
  }
}

function Layer({ url, layerId, onPick, selected, hover }) {
  const { scene } = useGLTF(url, 'draco/')
  const original = useRef(new Map())
  const hoveredRef = useRef(null)

  // Lần tải đầu: mỗi mesh có vật liệu độc lập (tránh màu nổi bật lan sang), ghi lại màu gốc nướng vào model.
  useMemo(() => {
    scene.traverse((o) => {
      if (o.isMesh && o.material) {
        o.material = (Array.isArray(o.material) ? o.material[0] : o.material).clone()
        const m = o.material
        m.metalness = 0
        if (m.roughness === undefined || m.roughness === 1) m.roughness = 0.65
        if (m.color) original.current.set(o.uuid, m.color.clone())
      }
    })
  }, [scene, layerId])

  // Làm nổi bật khi click chọn (chỉ thực hiện khi lựa chọn thay đổi, theo App render lại)
  scene.traverse((o) => {
    if (o.isMesh && o.material && o.material.color) {
      if (selected && o === selected) o.material.color.copy(SELECT_COLOR)
      else if (original.current.has(o.uuid)) o.material.color.copy(original.current.get(o.uuid))
    }
  })

  const clearHover = () => {
    if (hoveredRef.current) { setHover(hoveredRef.current, false); hoveredRef.current = null }
  }

  return (
    <primitive
      object={scene}
      onClick={(e) => { e.stopPropagation(); onPick(e.object) }}
      onPointerMove={(e) => {
        e.stopPropagation()
        const o = e.object
        if (o !== hoveredRef.current) {
          setHover(hoveredRef.current, false)
          setHover(o, true)
          hoveredRef.current = o
          document.body.style.cursor = 'pointer'
        }
        hover.show(o.name, e.nativeEvent.clientX, e.nativeEvent.clientY)
      }}
      onPointerOut={() => {
        clearHover()
        document.body.style.cursor = 'default'
        hover.hide()
      }}
    />
  )
}

function SourceList() {
  return (
    <div className="sources">
      <div className="lbl">Nguồn dữ liệu</div>
      <ul>
        {SOURCES.map((s) => (
          <li key={s.key}>
            <span className="tag">{s.label}</span>
            <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a>
            <em>{s.note}</em>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Panel({ info, active, toggle, layers }) {
  const [showSources, setShowSources] = useState(false)

  return (
    <aside className="panel">
      <h1>Cấu trúc cơ thể người</h1>
      <p className="sub">Bản đồ giải phẫu 3D tương tác · Bao gồm 1347 cấu trúc</p>

      <div className="layers">
        {layers.map((l) => (
          <button
            key={l.id}
            className={active.has(l.id) ? 'chip on' : 'chip'}
            onClick={() => toggle(l.id)}
          >{l.zh}</button>
        ))}
      </div>

      {info ? (
        <div className="card">
          <div className="zh">{info.zh || info.en}</div>
          <div className="en">{info.en}</div>
          {info.la && <div className="la">{info.la}</div>}
          {info.sys && <div className="row"><span>Hệ thống thuộc về</span><b>{info.sys}</b></div>}
          {info.side && <div className="row"><span>Bên (trái/phải)</span><b>{info.side.replace(/[（）]/g, '')}</b></div>}
          {info.intro && (
            <div className="block"><div className="lbl">Giới thiệu</div><p>{info.intro}</p></div>
          )}
          {info.func && (
            <div className="block"><div className="lbl">Chức năng</div><p>{info.func}</p></div>
          )}
          <div className="block refs">
            <div className="lbl">Nguồn</div>
            <p>
              Tên tiếng Trung theo 《Thuật ngữ Giải phẫu Cơ thể Người》 ấn bản 2, tên Latin theo Terminologia Anatomica 2.
              {info.wd && (
                <>
                  {' '}
                  <a href={`https://www.wikidata.org/wiki/${info.wd}`} target="_blank" rel="noreferrer">
                    Kiểm tra mục này trên Wikidata ({info.wd})
                  </a>
                </>
              )}
            </p>
          </div>
          {!info.zh && (
            <div className="todo">Cấu trúc này chưa có mô tả tiếng Trung.</div>
          )}
        </div>
      ) : (
        <div className="hint">Di chuột lên cấu trúc bất kỳ để hiện tên, click để chọn xem chi tiết.<br />Kéo để xoay, cuộn chuột để phóng to/thu nhỏ, phía trên để chuyển lớp.</div>
      )}

      <div className="attribution">
        <button className="link" onClick={() => setShowSources((v) => !v)}>
          {showSources ? 'Thu gọn nguồn dữ liệu ▲' : 'Xem tất cả nguồn dữ liệu ▼'}
        </button>
        {showSources && <SourceList />}
        <p>
          Nguồn model: <a href="https://github.com/Z-Anatomy" target="_blank" rel="noreferrer">Z-Anatomy</a>
          （CC BY-SA 4.0，源自 BodyParts3D）。
        </p>
      </div>
    </aside>
  )
}

export default function App() {
  const [selected, setSelected] = useState(null)
  const [info, setInfo] = useState(null)
  const [active, setActive] = useState(new Set(['skeleton']))
  const tipRef = useRef(null)

  // Tooltip kiểu mệnh lệnh: ghi trực tiếp vào DOM, không qua React state, đảm bảo hover mượt.
  const hover = useMemo(() => ({
    show: (name, x, y) => {
      const el = tipRef.current
      if (!el) return
      const r = lookup(name)
      el.textContent = r.zh ? `${r.zh}  ·  ${r.en}` : r.en
      el.style.left = x + 'px'
      el.style.top = y + 'px'
      el.style.opacity = '1'
    },
    hide: () => { if (tipRef.current) tipRef.current.style.opacity = '0' },
  }), [])

  const onPick = (mesh) => { setSelected(mesh); setInfo(lookup(mesh.name)) }
  const toggle = (id) => setActive((prev) => {
    const next = new Set(prev)
    next.has(id) ? next.delete(id) : next.add(id)
    return next
  })

  const visible = LAYERS.filter((l) => active.has(l.id))

  return (
    <div className="app">
      <div className="stage">
        <Canvas camera={{ position: [0, 1, 3], fov: 45 }} onPointerMissed={() => { setSelected(null); setInfo(null) }}>
          <hemisphereLight args={['#ffffff', '#4a5568', 0.9]} />
          <ambientLight intensity={0.35} />
          <directionalLight position={[3, 5, 2]} intensity={1.1} />
          <directionalLight position={[-4, 1, -3]} intensity={0.5} />
          <directionalLight position={[0, -3, 2]} intensity={0.3} />
          <Suspense fallback={<Html center>Đang tải model…</Html>}>
            <Bounds fit clip observe margin={1.1} key={visible.map((v) => v.id).join(',')}>
              {visible.map((l) => (
                <Layer key={l.id} url={l.url} layerId={l.id} onPick={onPick} selected={selected} hover={hover} />
              ))}
            </Bounds>
          </Suspense>
          <OrbitControls makeDefault enableDamping />
        </Canvas>
        <div ref={tipRef} className="tooltip" />
      </div>
      <Panel info={info} active={active} toggle={toggle} layers={LAYERS} />
    </div>
  )
}