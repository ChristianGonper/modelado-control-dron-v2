import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { Maximize2, Minimize2 } from "lucide-react";
import { TrajectorySample } from "../types";

export interface TrajectoryViewer3DProps {
  nominalPath?: [number, number, number][];
  isTransitionFlags?: boolean[];
  initialPosition?: [number, number, number];
  runsTrajectory?: Record<string, TrajectorySample[]>;
  visibleControllers?: Record<string, boolean>;
  currentTime?: number;
  accessibilitySummary?: string;
  className?: string;
  showSpatialSummary?: boolean;
  showLegend?: boolean;
  children?: React.ReactNode;
}

const CONTROLLER_COLORS: Record<string, number> = {
  classic: 0x0284c7, // Sky / Electric Blue
  mlp: 0x10b981,     // Vivid Emerald Green
  gru: 0xf59e0b,     // Vivid Amber Orange
  lstm: 0x8b5cf6,    // Vivid Purple / Violet
};

/**
 * Creates a procedural 3D Quadcopter model with carbon frame, central avionics hub,
 * 4 motors, spinning rotor discs and a forward heading indicator.
 * Distinguishes controllers geometrically in addition to color:
 * - classic (PD): Spherical dome
 * - mlp: Flat cylinder cap
 * - gru: Angular box canopy
 * - lstm: Diamond / Octahedron canopy
 */
const createDroneGroup = (cid: string, color: number, isStopped: boolean = false) => {
  const drone = new THREE.Group();

  // 1. Carbon fiber central hub (fuselage)
  const hubGeo = new THREE.CylinderGeometry(0.06, 0.07, 0.035, 12);
  const hubMat = new THREE.MeshStandardMaterial({
    color: 0x0f172a,
    roughness: 0.4,
    metalness: 0.6,
  });
  const hubMesh = new THREE.Mesh(hubGeo, hubMat);
  hubMesh.rotation.x = Math.PI / 2;
  drone.add(hubMesh);

  // 2. Controller accent dome / canopy with distinctive geometry per controller
  let domeGeo: THREE.BufferGeometry;
  if (cid === "mlp") {
    // Flat cylinder cap
    domeGeo = new THREE.CylinderGeometry(0.04, 0.045, 0.025, 12);
  } else if (cid === "gru") {
    // Angular box canopy
    domeGeo = new THREE.BoxGeometry(0.065, 0.065, 0.03);
  } else if (cid === "lstm") {
    // Diamond / Octahedron canopy
    domeGeo = new THREE.OctahedronGeometry(0.045, 0);
  } else {
    // Default classic (PD): Spherical dome
    domeGeo = new THREE.SphereGeometry(0.042, 12, 12, 0, Math.PI * 2, 0, Math.PI / 2);
  }

  const domeMat = new THREE.MeshStandardMaterial({
    color: color,
    roughness: 0.2,
    metalness: 0.4,
  });
  const domeMesh = new THREE.Mesh(domeGeo, domeMat);
  domeMesh.rotation.x = -Math.PI / 2;
  domeMesh.position.z = 0.016;
  drone.add(domeMesh);

  // 3. Four diagonal carbon arms in "X" layout (semi-span 0.16m, total span 0.32m)
  const armMat = new THREE.MeshStandardMaterial({
    color: 0x1e293b,
    roughness: 0.5,
    metalness: 0.5,
  });
  const armGeo = new THREE.BoxGeometry(0.32, 0.016, 0.012);

  const arm1 = new THREE.Mesh(armGeo, armMat);
  arm1.rotation.z = Math.PI / 4;
  drone.add(arm1);

  const arm2 = new THREE.Mesh(armGeo, armMat);
  arm2.rotation.z = -Math.PI / 4;
  drone.add(arm2);

  // 4. Four motor nacelles and translucent rotor discs
  const motorGeo = new THREE.CylinderGeometry(0.018, 0.018, 0.024, 10);
  const motorMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.3 });

  const rotorGeo = new THREE.CircleGeometry(0.065, 16);
  const rotorMat = new THREE.MeshBasicMaterial({
    color: color,
    transparent: true,
    opacity: 0.5,
    side: THREE.DoubleSide,
  });

  const rotorArmDist = 0.113; // 0.16 * cos(45 deg)
  const motorPositions = [
    [rotorArmDist, rotorArmDist],
    [-rotorArmDist, rotorArmDist],
    [-rotorArmDist, -rotorArmDist],
    [rotorArmDist, -rotorArmDist],
  ];

  motorPositions.forEach(([mx, my]) => {
    const m = new THREE.Mesh(motorGeo, motorMat);
    m.rotation.x = Math.PI / 2;
    m.position.set(mx, my, 0.005);
    drone.add(m);

    const r = new THREE.Mesh(rotorGeo, rotorMat);
    r.position.set(mx, my, 0.02);
    drone.add(r);
  });

  // 5. Forward Heading Indicator (Arrow pointing in +X direction)
  const arrowGeo = new THREE.ConeGeometry(0.025, 0.06, 8);
  const arrowMat = new THREE.MeshBasicMaterial({ color: color });
  const arrowMesh = new THREE.Mesh(arrowGeo, arrowMat);
  arrowMesh.rotation.z = -Math.PI / 2;
  arrowMesh.position.set(0.09, 0, 0.01);
  drone.add(arrowMesh);

  // 6. Early-termination alert ring if stopped
  if (isStopped) {
    const alertGeo = new THREE.RingGeometry(0.18, 0.22, 16);
    const alertMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85,
    });
    const alertMesh = new THREE.Mesh(alertGeo, alertMat);
    alertMesh.position.z = 0.035;
    drone.add(alertMesh);
  }

  return drone;
};

export const TrajectoryViewer3D: React.FC<TrajectoryViewer3DProps> = ({
  nominalPath = [],
  isTransitionFlags = [],
  initialPosition,
  runsTrajectory = {},
  visibleControllers = { classic: true, mlp: true, gru: false, lstm: false },
  currentTime = 0,
  accessibilitySummary = "",
  className = "w-full h-[420px]",
  showSpatialSummary = true,
  showLegend = false,
  children,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const animationFrameId = useRef<number | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Dynamic objects container
  const trailsGroupRef = useRef<THREE.Group>(new THREE.Group());
  const markersGroupRef = useRef<THREE.Group>(new THREE.Group());

  // Mouse & Touch orbit and pan control state
  const isDragging = useRef(false);
  const dragMode = useRef<"orbit" | "pan">("orbit");
  const previousMousePosition = useRef({ x: 0, y: 0 });
  const touchStartDist = useRef<number | null>(null);
  const touchStartCenter = useRef<{ x: number; y: number } | null>(null);
  const cameraDistance = useRef(9.0);
  const cameraAngle = useRef({ theta: Math.PI / 4, phi: Math.PI / 3 });
  const cameraTarget = useRef({ x: 0, y: 0, z: 1.5 });

  // Camera update function
  const updateCameraPosition = () => {
    if (!cameraRef.current) return;
    const r = cameraDistance.current;
    const { theta, phi } = cameraAngle.current;
    const target = cameraTarget.current;
    cameraRef.current.position.x = target.x + r * Math.sin(phi) * Math.sin(theta);
    cameraRef.current.position.y = target.y + r * Math.sin(phi) * Math.cos(theta);
    cameraRef.current.position.z = target.z + r * Math.cos(phi);
    cameraRef.current.lookAt(target.x, target.y, target.z);
  };

  // Pan camera across the camera viewing plane
  const panCamera = (deltaX: number, deltaY: number) => {
    if (!cameraRef.current) return;
    const factor = cameraDistance.current * 0.0016;

    const camera = cameraRef.current;
    const right = new THREE.Vector3();
    const up = new THREE.Vector3();
    camera.matrixWorld.extractBasis(right, up, new THREE.Vector3());

    // deltaX: positive means drag to right -> scene moves right (target shifts in -right direction)
    // deltaY: positive means drag downwards -> scene moves down (target shifts in +up direction)
    const panOffset = new THREE.Vector3()
      .addScaledVector(right, -deltaX * factor)
      .addScaledVector(up, deltaY * factor);

    cameraTarget.current.x += panOffset.x;
    cameraTarget.current.y += panOffset.y;
    cameraTarget.current.z += panOffset.z;

    updateCameraPosition();
  };

  const toggleFullscreen = async () => {
    if (!containerRef.current) return;
    try {
      if (!document.fullscreenElement && !isFullscreen) {
        if (containerRef.current.requestFullscreen) {
          await containerRef.current.requestFullscreen();
        }
        setIsFullscreen(true);
      } else {
        if (document.fullscreenElement && document.exitFullscreen) {
          await document.exitFullscreen();
        }
        setIsFullscreen(false);
      }
    } catch {
      setIsFullscreen((prev) => !prev);
    }
  };

  // Fullscreen change listener
  useEffect(() => {
    const handleFsChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
      setTimeout(() => {
        if (!mountRef.current || !rendererRef.current || !cameraRef.current) return;
        const w = mountRef.current.clientWidth;
        const h = mountRef.current.clientHeight;
        if (w === 0 || h === 0) return;
        cameraRef.current.aspect = w / h;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(w, h);
      }, 50);
    };
    document.addEventListener("fullscreenchange", handleFsChange);
    return () => document.removeEventListener("fullscreenchange", handleFsChange);
  }, []);

  // Esc key fallback for CSS fullscreen
  useEffect(() => {
    const handleKeyDownEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDownEsc);
    return () => window.removeEventListener("keydown", handleKeyDownEsc);
  }, [isFullscreen]);

  // 1. Initial Scene Setup
  useEffect(() => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f8fc); // #F5F8FC
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.up.set(0, 0, 1);
    cameraRef.current = camera;
    updateCameraPosition();

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(5, 5, 10);
    scene.add(dirLight);

    // Ground plane & Grid on Z=0
    const gridHelper = new THREE.GridHelper(16, 32, 0x0284c7, 0xd9e3f0);
    gridHelper.rotation.x = Math.PI / 2;
    scene.add(gridHelper);

    // Coordinate Axes Indicator
    const axesHelper = new THREE.AxesHelper(1.0);
    axesHelper.position.set(-6, -6, 0.02);
    scene.add(axesHelper);

    scene.add(trailsGroupRef.current);
    scene.add(markersGroupRef.current);

    // Render loop
    const animate = () => {
      renderer.render(scene, camera);
      animationFrameId.current = requestAnimationFrame(animate);
    };
    animate();

    const handleResize = () => {
      if (!mountRef.current || !renderer || !camera) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      if (w === 0 || h === 0) return;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // Active wheel listener with passive: false to prevent whole-page scrolling on 3D zoom
    const dom = mountRef.current;
    const onWheelNative = (e: WheelEvent) => {
      e.preventDefault();
      e.stopPropagation();
      cameraDistance.current = Math.max(3.0, Math.min(25.0, cameraDistance.current + e.deltaY * 0.008));
      updateCameraPosition();
    };
    dom?.addEventListener("wheel", onWheelNative, { passive: false });

    return () => {
      window.removeEventListener("resize", handleResize);
      dom?.removeEventListener("wheel", onWheelNative);
      if (animationFrameId.current) cancelAnimationFrame(animationFrameId.current);
      if (renderer.domElement && mountRef.current) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // 2. Smooth Orbit, Pan & Zoom Navigation (Mouse, Touch, and Keyboard)
  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    previousMousePosition.current = { x: e.clientX, y: e.clientY };
    // Right click (button === 2), Middle click (button === 1), or Shift + Click activates Pan
    if (e.button === 2 || e.button === 1 || e.shiftKey) {
      dragMode.current = "pan";
    } else {
      dragMode.current = "orbit";
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current) return;
    const deltaX = e.clientX - previousMousePosition.current.x;
    const deltaY = e.clientY - previousMousePosition.current.y;

    if (dragMode.current === "pan" || e.buttons === 2 || e.buttons === 4 || e.shiftKey) {
      panCamera(deltaX, deltaY);
    } else {
      cameraAngle.current.theta -= deltaX * 0.0035;
      cameraAngle.current.phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, cameraAngle.current.phi - deltaY * 0.0035));
      updateCameraPosition();
    }

    previousMousePosition.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDragging.current = false;
    dragMode.current = "orbit";
  };

  // Touch handlers for mobile / tablet devices (1-finger drag orbit, 2-finger pan & pinch zoom)
  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      isDragging.current = true;
      dragMode.current = "orbit";
      previousMousePosition.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
      touchStartDist.current = null;
      touchStartCenter.current = null;
    } else if (e.touches.length === 2) {
      isDragging.current = false;
      touchStartDist.current = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      touchStartCenter.current = {
        x: (e.touches[0].clientX + e.touches[1].clientX) / 2,
        y: (e.touches[0].clientY + e.touches[1].clientY) / 2,
      };
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length === 1 && isDragging.current) {
      const deltaX = e.touches[0].clientX - previousMousePosition.current.x;
      const deltaY = e.touches[0].clientY - previousMousePosition.current.y;

      cameraAngle.current.theta -= deltaX * 0.005;
      cameraAngle.current.phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, cameraAngle.current.phi - deltaY * 0.005));

      updateCameraPosition();
      previousMousePosition.current = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    } else if (e.touches.length === 2) {
      // 2-finger pinch zoom
      const currentDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      if (touchStartDist.current !== null) {
        const delta = touchStartDist.current - currentDist;
        cameraDistance.current = Math.max(3.0, Math.min(25.0, cameraDistance.current + delta * 0.02));
      }
      touchStartDist.current = currentDist;

      // 2-finger pan
      const currentCenter = {
        x: (e.touches[0].clientX + e.touches[1].clientX) / 2,
        y: (e.touches[0].clientY + e.touches[1].clientY) / 2,
      };
      if (touchStartCenter.current !== null) {
        const deltaX = currentCenter.x - touchStartCenter.current.x;
        const deltaY = currentCenter.y - touchStartCenter.current.y;
        panCamera(deltaX, deltaY);
      }
      touchStartCenter.current = currentCenter;
    }
  };

  const handleTouchEnd = () => {
    isDragging.current = false;
    touchStartDist.current = null;
    touchStartCenter.current = null;
    dragMode.current = "orbit";
  };

  // Keyboard navigation for accessible camera control (including Shift+Arrow Pan)
  const handleKeyDown = (e: React.KeyboardEvent) => {
    let handled = true;
    switch (e.key) {
      case "ArrowLeft":
        if (e.shiftKey) panCamera(-30, 0);
        else cameraAngle.current.theta += 0.08;
        break;
      case "ArrowRight":
        if (e.shiftKey) panCamera(30, 0);
        else cameraAngle.current.theta -= 0.08;
        break;
      case "ArrowUp":
        if (e.shiftKey) panCamera(0, -30);
        else cameraAngle.current.phi = Math.max(0.1, cameraAngle.current.phi - 0.06);
        break;
      case "ArrowDown":
        if (e.shiftKey) panCamera(0, 30);
        else cameraAngle.current.phi = Math.min(Math.PI / 2 - 0.05, cameraAngle.current.phi + 0.06);
        break;
      case "+":
      case "=":
      case "PageUp":
        cameraDistance.current = Math.max(3.0, cameraDistance.current - 0.8);
        break;
      case "-":
      case "_":
      case "PageDown":
        cameraDistance.current = Math.min(25.0, cameraDistance.current + 0.8);
        break;
      case "r":
      case "R":
      case "Home":
        cameraAngle.current = { theta: Math.PI / 4, phi: Math.PI / 3 };
        cameraDistance.current = 9.0;
        cameraTarget.current = { x: 0, y: 0, z: 1.5 };
        break;
      default:
        handled = false;
    }
    if (handled) {
      e.preventDefault();
      updateCameraPosition();
    }
  };

  // 3. Update Trajectory Paths & Nominal Reference
  useEffect(() => {
    const group = trailsGroupRef.current;
    while (group.children.length > 0) {
      const child = group.children[0] as any;
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
      group.remove(child);
    }

    // A. Draw Start Point Helipad / Landing Pad (Expanded diameter for clear visibility)
    if (initialPosition) {
      const padGeo = new THREE.RingGeometry(0.35, 0.44, 32);
      const padMat = new THREE.MeshBasicMaterial({ color: 0x0284c7, side: THREE.DoubleSide });
      const padMesh = new THREE.Mesh(padGeo, padMat);
      padMesh.position.set(initialPosition[0], initialPosition[1], 0.01);
      group.add(padMesh);

      const innerGeo = new THREE.CircleGeometry(0.16, 24);
      const innerMat = new THREE.MeshBasicMaterial({ color: 0x0284c7, opacity: 0.35, transparent: true, side: THREE.DoubleSide });
      const innerMesh = new THREE.Mesh(innerGeo, innerMat);
      innerMesh.position.set(initialPosition[0], initialPosition[1], 0.01);
      group.add(innerMesh);

      const stemGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(initialPosition[0], initialPosition[1], 0.01),
        new THREE.Vector3(initialPosition[0], initialPosition[1], initialPosition[2]),
      ]);
      const stemMat = new THREE.LineDashedMaterial({ color: 0x0284c7, dashSize: 0.1, gapSize: 0.06 });
      const stemLine = new THREE.Line(stemGeo, stemMat);
      stemLine.computeLineDistances();
      group.add(stemLine);

      // Replace static cube/octahedron with the 3D Quadcopter Drone model
      if (Object.keys(runsTrajectory).length === 0) {
        const drone = createDroneGroup("classic", 0x0284c7, false);
        drone.position.set(initialPosition[0], initialPosition[1], initialPosition[2]);
        if (nominalPath.length >= 2) {
          const dx = nominalPath[1][0] - nominalPath[0][0];
          const dy = nominalPath[1][1] - nominalPath[0][1];
          if (Math.hypot(dx, dy) > 0.01) {
            drone.rotation.z = Math.atan2(dy, dx);
          }
        }
        group.add(drone);
      }
    }

    // B. Draw Nominal Trajectory (Slate solid path or dashed transitions)
    if (nominalPath.length > 1) {
      let currentPoints: THREE.Vector3[] = [];
      let currentIsTrans = isTransitionFlags[0] || false;

      const flushSegment = (pts: THREE.Vector3[], isTrans: boolean) => {
        if (pts.length < 2) return;
        const geom = new THREE.BufferGeometry().setFromPoints(pts);
        if (isTrans) {
          const mat = new THREE.LineDashedMaterial({
            color: 0x64748b,
            dashSize: 0.15,
            gapSize: 0.1,
            linewidth: 2,
          });
          const line = new THREE.Line(geom, mat);
          line.computeLineDistances();
          group.add(line);
        } else {
          const mat = new THREE.LineBasicMaterial({
            color: 0x334155, // Clean dark slate stroke for nominal path
            linewidth: 2.5,
          });
          group.add(new THREE.Line(geom, mat));
        }
      };

      nominalPath.forEach((pt, idx) => {
        const v = new THREE.Vector3(pt[0], pt[1], pt[2]);
        const trans = isTransitionFlags[idx] || false;
        if (trans !== currentIsTrans && currentPoints.length > 0) {
          currentPoints.push(v);
          flushSegment(currentPoints, currentIsTrans);
          currentPoints = [v];
          currentIsTrans = trans;
        } else {
          currentPoints.push(v);
        }
      });
      if (currentPoints.length >= 2) {
        flushSegment(currentPoints, currentIsTrans);
      }
    }

    // C. Draw Real Executed Trajectories
    Object.entries(runsTrajectory).forEach(([cid, samples]) => {
      if (!visibleControllers[cid] || samples.length < 2) return;

      const pts = samples.map((s) => new THREE.Vector3(s.pos[0], s.pos[1], s.pos[2]));
      const geom = new THREE.BufferGeometry().setFromPoints(pts);
      const color = CONTROLLER_COLORS[cid] || 0x0284c7;

      if (cid === "gru") {
        const mat = new THREE.LineDashedMaterial({ color, dashSize: 0.2, gapSize: 0.1, linewidth: 2 });
        const line = new THREE.Line(geom, mat);
        line.computeLineDistances();
        group.add(line);
      } else if (cid === "lstm") {
        const mat = new THREE.LineDashedMaterial({ color, dashSize: 0.08, gapSize: 0.08, linewidth: 2 });
        const line = new THREE.Line(geom, mat);
        line.computeLineDistances();
        group.add(line);
      } else {
        const mat = new THREE.LineBasicMaterial({ color, linewidth: 3 });
        group.add(new THREE.Line(geom, mat));
      }
    });
  }, [nominalPath, isTransitionFlags, initialPosition, runsTrajectory, visibleControllers]);

  // 4. Update Time-Synchronized Quadcopters
  useEffect(() => {
    const group = markersGroupRef.current;
    while (group.children.length > 0) {
      const child = group.children[0] as any;
      if (child.geometry) child.geometry.dispose();
      if (child.material) child.material.dispose();
      group.remove(child);
    }

    Object.entries(runsTrajectory).forEach(([cid, samples]) => {
      if (!visibleControllers[cid] || samples.length === 0) return;

      let targetSample = samples[0];
      for (let i = 0; i < samples.length; i++) {
        if (samples[i].time_s <= currentTime) {
          targetSample = samples[i];
        } else {
          break;
        }
      }

      const lastSample = samples[samples.length - 1];
      const isStopped = currentTime > lastSample.time_s;
      const effectiveSample = isStopped ? lastSample : targetSample;

      const color = CONTROLLER_COLORS[cid] || 0x0284c7;

      // 3D Procedural Quadcopter Model with distinct geometry per controller
      const droneGroup = createDroneGroup(cid, color, isStopped);
      droneGroup.position.set(effectiveSample.pos[0], effectiveSample.pos[1], effectiveSample.pos[2]);

      // Height projection stalk to ground
      const stalkGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, 0, -effectiveSample.pos[2]),
      ]);
      const stalkMat = new THREE.LineBasicMaterial({ color, opacity: 0.35, transparent: true });
      droneGroup.add(new THREE.Line(stalkGeo, stalkMat));

      // Ground shadow disk
      const shadowGeo = new THREE.CircleGeometry(0.18, 16);
      const shadowMat = new THREE.MeshBasicMaterial({ color: 0xd9e3f0, transparent: true, opacity: 0.6 });
      const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
      shadowMesh.position.set(0, 0, -effectiveSample.pos[2] + 0.01);
      droneGroup.add(shadowMesh);

      group.add(droneGroup);
    });
  }, [runsTrajectory, visibleControllers, currentTime]);

  return (
    <div
      ref={containerRef}
      className={
        isFullscreen
          ? "fixed inset-0 z-50 bg-[#F5F8FC] w-screen h-screen flex flex-col p-4 box-border"
          : "flex flex-col gap-2"
      }
    >
      <div
        ref={mountRef}
        tabIndex={0}
        role="region"
        aria-label="Visualizador 3D de trayectoria de vuelo. Usa click izquierdo para rotar, click derecho o Shift para desplazar (pan), rueda para zoom y R para reiniciar cámara."
        className={`${
          isFullscreen ? "flex-1 w-full h-full min-h-0" : className
        } relative rounded-xl border border-aerolab-border bg-aerolab-canvas overflow-hidden cursor-grab active:cursor-grabbing select-none touch-none focus-visible:ring-2 focus-visible:ring-aerolab-action`}
        onContextMenu={(e) => e.preventDefault()}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onTouchCancel={handleTouchEnd}
        onKeyDown={handleKeyDown}
      >
        {/* Minimal Interactive Mode Indicator with keyboard hint */}
        <div className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm px-2.5 py-1 rounded-md border border-aerolab-border shadow-xs text-[11px] font-mono text-aerolab-secondary flex items-center gap-1.5 z-10">
          <span className="w-1.5 h-1.5 rounded-full bg-aerolab-action animate-pulse" />
          <span>Vista 3D interactiva</span>
          <span className="hidden sm:inline text-[10px] text-slate-400 border-l border-slate-200 pl-1.5 ml-0.5">
            Click izq: rotar • Click dcho / Shift: pan • scroll zoom • R reset
          </span>
        </div>

        {/* Top-right controls: Fullscreen button & Floating Legend */}
        <div className="absolute top-3 right-3 flex flex-col items-end gap-2 z-10">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              toggleFullscreen();
            }}
            className="bg-white/95 hover:bg-white backdrop-blur-sm p-1.5 rounded-lg border border-aerolab-border shadow-xs text-aerolab-secondary hover:text-aerolab-action transition-all cursor-pointer flex items-center gap-1.5 text-xs font-medium"
            title={isFullscreen ? "Salir de pantalla completa (Esc)" : "Ver a pantalla completa"}
            aria-label={isFullscreen ? "Salir de pantalla completa" : "Ver a pantalla completa"}
          >
            {isFullscreen ? (
              <>
                <Minimize2 className="w-4 h-4" />
                <span className="text-[11px] hidden sm:inline">Salir</span>
              </>
            ) : (
              <>
                <Maximize2 className="w-4 h-4" />
                <span className="text-[11px] hidden sm:inline">Pantalla completa</span>
              </>
            )}
          </button>

          {showLegend && (
            <div className="bg-white/95 backdrop-blur-sm px-3 py-2 rounded-lg border border-aerolab-border shadow-xs flex flex-col gap-1 text-[11px]">
              <div className="flex items-center gap-2">
                <span className="w-3.5 h-0.5 bg-[#334155] rounded-full" />
                <span className="font-semibold text-aerolab-text">Nominal</span>
              </div>
              {Object.entries({
                classic: { name: "PD", color: "#0284C7", style: "—" },
                mlp: { name: "MLP", color: "#10B981", style: "—" },
                gru: { name: "GRU", color: "#F59E0B", style: "- -" },
                lstm: { name: "LSTM", color: "#8B5CF6", style: "···" },
              }).map(([cid, meta]) => {
                if (!visibleControllers[cid]) return null;
                return (
                  <div key={cid} className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: meta.color }} />
                    <span className="font-mono text-aerolab-text font-medium">{meta.name}</span>
                    <span className="text-[9px] font-mono text-slate-400 font-bold">({meta.style})</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Children passed into viewer (e.g. playback bar in fullscreen or normal) */}
      {children && (
        <div className={isFullscreen ? "mt-3 shrink-0" : ""}>
          {children}
        </div>
      )}

      {/* Accessible Text Alternative & Essential Spatial Summary */}
      {!isFullscreen && showSpatialSummary && accessibilitySummary && (
        <div
          role="status"
          aria-live="polite"
          className="text-xs text-aerolab-secondary bg-white px-3 py-2 rounded-lg border border-aerolab-border flex flex-wrap items-center justify-between gap-2"
        >
          <div className="font-mono text-[11px] text-aerolab-secondary">
            {accessibilitySummary}
          </div>
          {currentTime > 0 && (
            <div className="font-mono text-aerolab-action font-semibold text-xs">
              t = {currentTime.toFixed(2)} s
            </div>
          )}
        </div>
      )}
    </div>
  );
};
