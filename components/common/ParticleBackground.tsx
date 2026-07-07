import { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  opacity: number
  twinkleSpeed: number
  twinkleOffset: number
}

interface MouseStar {
  x: number
  y: number
  size: number
  opacity: number
}

export default function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particlesRef = useRef<Particle[]>([])
  const mouseRef = useRef<MouseStar | null>(null)
  const mousePosRef = useRef({ x: -100, y: -100 })
  const animationRef = useRef<number>(0)

  useEffect(() => {
    const canvas = canvasRef.current!
    const ctx = canvas.getContext('2d')!

    let width = window.innerWidth
    let height = window.innerHeight

    const resize = () => {
      width = window.innerWidth
      height = window.innerHeight
      canvas.width = width
      canvas.height = height
      initParticles()
    }

    // 初始化背景星星
    const initParticles = () => {
      const count = Math.floor((width * height) / 5000) // 根据屏幕大小适配数量
      particlesRef.current = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 2 + 0.5,
        opacity: Math.random() * 0.6 + 0.2,
        twinkleSpeed: Math.random() * 0.02 + 0.005,
        twinkleOffset: Math.random() * Math.PI * 2,
      }))
    }

    // 绘制单个星星
    const drawStar = (x: number, y: number, size: number, opacity: number, isMouse: boolean = false) => {
      ctx.save()
      ctx.globalAlpha = opacity
      ctx.fillStyle = isMouse ? '#88ccff' : '#aac8ff'

      // 绘制四角星芒
      const spikeLength = size * 3
      ctx.beginPath()
      for (let i = 0; i < 4; i++) {
        const angle = (i * Math.PI) / 2
        const x1 = x + Math.cos(angle) * spikeLength
        const y1 = y + Math.sin(angle) * spikeLength
        ctx.moveTo(x, y)
        ctx.lineTo(x1, y1)
      }
      ctx.strokeStyle = isMouse ? 'rgba(136,204,255,0.6)' : 'rgba(170,200,255,0.4)'
      ctx.lineWidth = 1.2
      ctx.stroke()

      // 绘制圆形光晕
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, size * 4)
      gradient.addColorStop(0, isMouse ? 'rgba(136,204,255,1)' : 'rgba(170,200,255,0.9)')
      gradient.addColorStop(0.3, isMouse ? 'rgba(100,170,255,0.6)' : 'rgba(120,160,255,0.4)')
      gradient.addColorStop(1, 'rgba(100,150,255,0)')
      ctx.beginPath()
      ctx.arc(x, y, size * 4, 0, Math.PI * 2)
      ctx.fillStyle = gradient
      ctx.fill()

      // 核心亮点
      ctx.beginPath()
      ctx.arc(x, y, size, 0, Math.PI * 2)
      ctx.fillStyle = isMouse ? '#ffffff' : 'rgba(200,220,255,0.9)'
      ctx.fill()

      ctx.restore()
    }

    // 绘制连接线
    // 绘制连接线
    const drawConnection = (x1: number, y1: number, x2: number, y2: number, opacity: number) => {
      const dist = Math.hypot(x2 - x1, y2 - y1)
      if (dist > 200) return

      const alpha = opacity * (1 - dist / 200)

      ctx.save()
      // 发光外层
      ctx.globalAlpha = alpha * 0.3
      ctx.strokeStyle = 'rgba(100,150,255,0.6)'
      ctx.lineWidth = 3
      ctx.shadowColor = 'rgba(100,150,255,0.8)'
      ctx.shadowBlur = 6
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.stroke()

      // 实线内层
      ctx.shadowBlur = 0
      ctx.globalAlpha = alpha
      ctx.strokeStyle = 'rgba(180,210,255,0.9)'
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.moveTo(x1, y1)
      ctx.lineTo(x2, y2)
      ctx.stroke()
      ctx.restore()
    }

    // 动画循环
    const animate = (timestamp: number) => {
      ctx.clearRect(0, 0, width, height)

      const particles = particlesRef.current
      const mouse = mouseRef.current
      const mx = mousePosRef.current.x
      const my = mousePosRef.current.y

      // 更新并绘制背景星星
      const nearbyParticles: { x: number; y: number; dist: number; index: number }[] = []

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i]

        // 移动
        p.x += p.vx
        p.y += p.vy

        // 边界回弹
        if (p.x < 0) p.x = width
        if (p.x > width) p.x = 0
        if (p.y < 0) p.y = height
        if (p.y > height) p.y = 0

        // 闪烁
        const twinkle = Math.sin(timestamp * p.twinkleSpeed + p.twinkleOffset) * 0.3 + 0.7
        const currentOpacity = p.opacity * twinkle

        drawStar(p.x, p.y, p.size, currentOpacity)

        // 计算与鼠标的距离，收集最近的几颗
        const dist = Math.hypot(p.x - mx, p.y - my)
        if (dist < 200 && mx > 0 && my > 0) {
          nearbyParticles.push({ x: p.x, y: p.y, dist, index: i })
        }
      }

      // 绘制鼠标星星
      if (mouse && mx > 0 && my > 0) {
        // 按距离排序，取最近的5颗
        nearbyParticles.sort((a, b) => a.dist - b.dist)
        const closest = nearbyParticles.slice(0, 5)

        // 绘制鼠标星星和最近星星之间的连线
        for (const np of closest) {
          drawConnection(mx, my, np.x, np.y, 0.7)
        }

        // 绘制最近几颗星星之间的连线
        for (let i = 0; i < closest.length; i++) {
          for (let j = i + 1; j < closest.length; j++) {
            drawConnection(closest[i].x, closest[i].y, closest[j].x, closest[j].y, 0.4)
          }
        }

        // 鼠标星星脉冲动画
        const pulse = Math.sin(timestamp * 0.005) * 0.3 + 0.7
        drawStar(mx, my, 3 * pulse, 1, true)
      }

      animationRef.current = requestAnimationFrame(animate)
    }

    // 鼠标事件
    const onMouseMove = (e: MouseEvent) => {
      mousePosRef.current = { x: e.clientX, y: e.clientY }
      if (!mouseRef.current) {
        mouseRef.current = { x: e.clientX, y: e.clientY, size: 3, opacity: 1 }
      }
    }

    const onMouseLeave = () => {
      mouseRef.current = null
      mousePosRef.current = { x: -100, y: -100 }
    }

    resize()
    window.addEventListener('resize', resize)
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseleave', onMouseLeave)

    animationRef.current = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(animationRef.current)
      window.removeEventListener('resize', resize)
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseleave', onMouseLeave)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 0,
        background: 'linear-gradient(to bottom, #0a0a1a 0%, #0f0f2e 30%, #1a1a3e 60%, #0d0d24 100%)',
      }}
    />
  )
}