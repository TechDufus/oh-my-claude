import { useEffect, useRef } from 'react'
import * as THREE from 'three'

// ASCII effect shader implementation
const AsciiShader = {
  uniforms: {
    tDiffuse: { value: null },
    resolution: { value: new THREE.Vector2() },
    charSize: { value: 8.0 },
  },
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform sampler2D tDiffuse;
    uniform vec2 resolution;
    uniform float charSize;
    varying vec2 vUv;

    float character(float n, vec2 p) {
      p = floor(p * vec2(4.0, 4.0) + 2.5);
      if (clamp(p.x, 0.0, 4.0) == p.x && clamp(p.y, 0.0, 4.0) == p.y) {
        float c = floor(mod(n / exp2(p.x + 5.0 * p.y), 2.0));
        return c;
      }
      return 0.0;
    }

    void main() {
      vec2 pix = gl_FragCoord.xy;
      vec2 cell = floor(pix / charSize) * charSize;
      vec2 uv = cell / resolution;

      vec4 col = texture2D(tDiffuse, uv);
      float gray = 0.299 * col.r + 0.587 * col.g + 0.114 * col.b;

      // ASCII character set mapped by brightness
      float n = 0.0;
      if (gray > 0.2) n = 4096.0;      // .
      if (gray > 0.3) n = 65600.0;     // :
      if (gray > 0.4) n = 332772.0;    // *
      if (gray > 0.5) n = 15255086.0;  // o
      if (gray > 0.6) n = 23385164.0;  // &
      if (gray > 0.7) n = 15252014.0;  // 8
      if (gray > 0.8) n = 13199452.0;  // @
      if (gray > 0.9) n = 11512810.0;  // #

      vec2 p = mod(pix / (charSize * 0.5), 2.0) - 1.0;
      float c = character(n, p);

      // Cyan color for ASCII characters
      vec3 asciiColor = vec3(0.0, 0.898, 0.8) * c * gray;

      gl_FragColor = vec4(asciiColor, 1.0);
    }
  `,
}

export default function AsciiHero() {
  const containerRef = useRef<HTMLDivElement>(null)
  const frameRef = useRef<number>(0)

  useEffect(() => {
    if (!containerRef.current) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight

    // Scene setup
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x050810)

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
    camera.position.z = 3

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Cube geometry
    const geometry = new THREE.BoxGeometry(1.5, 1.5, 1.5)
    const material = new THREE.MeshStandardMaterial({
      color: 0x00e5cc,
      metalness: 0.3,
      roughness: 0.4,
    })
    const cube = new THREE.Mesh(geometry, material)
    scene.add(cube)

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5)
    scene.add(ambientLight)

    const pointLight = new THREE.PointLight(0x00e5cc, 1, 100)
    pointLight.position.set(5, 5, 5)
    scene.add(pointLight)

    const pointLight2 = new THREE.PointLight(0xff4d4d, 0.5, 100)
    pointLight2.position.set(-5, -5, 5)
    scene.add(pointLight2)

    // Render target for ASCII effect
    const renderTarget = new THREE.WebGLRenderTarget(width, height)

    // ASCII post-processing setup
    const asciiMaterial = new THREE.ShaderMaterial({
      uniforms: {
        tDiffuse: { value: renderTarget.texture },
        resolution: { value: new THREE.Vector2(width, height) },
        charSize: { value: 10.0 },
      },
      vertexShader: AsciiShader.vertexShader,
      fragmentShader: AsciiShader.fragmentShader,
    })

    const quadGeometry = new THREE.PlaneGeometry(2, 2)
    const quadMesh = new THREE.Mesh(quadGeometry, asciiMaterial)
    const quadScene = new THREE.Scene()
    quadScene.add(quadMesh)

    const quadCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1)

    // Animation
    const animate = () => {
      frameRef.current = requestAnimationFrame(animate)

      if (cube) {
        cube.rotation.x += 0.005
        cube.rotation.y += 0.008
      }

      // Render scene to render target
      renderer.setRenderTarget(renderTarget)
      renderer.render(scene, camera)

      // Render ASCII effect
      renderer.setRenderTarget(null)
      renderer.render(quadScene, quadCamera)
    }

    animate()

    // Handle resize
    const handleResize = () => {
      if (!container || !camera || !renderer) return
      const newWidth = container.clientWidth
      const newHeight = container.clientHeight

      camera.aspect = newWidth / newHeight
      camera.updateProjectionMatrix()

      renderer.setSize(newWidth, newHeight)
      renderTarget.setSize(newWidth, newHeight)
      asciiMaterial.uniforms.resolution.value.set(newWidth, newHeight)
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      cancelAnimationFrame(frameRef.current)
      renderer.dispose()
      geometry.dispose()
      material.dispose()
      container.removeChild(renderer.domElement)
    }
  }, [])

  return (
    <div
      ref={containerRef}
      className="w-full h-[400px] md:h-[500px] relative"
      aria-label="3D ASCII cube animation"
    />
  )
}
