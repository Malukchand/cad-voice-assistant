import React, { Suspense, useMemo } from 'react';
import { Canvas, useLoader } from '@react-three/fiber';
import { OrbitControls, Stage, Grid, Environment } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import * as THREE from 'three';

const Model = ({ url, selectedId }: { url: string, selectedId: string | null }) => {
  // Load STL
  const geometry = useLoader(STLLoader, url);

  // Center geometry
  useMemo(() => {
    if (geometry) geometry.center();
  }, [geometry]);

  return (
    <mesh
      geometry={geometry}
      scale={[0.1, 0.1, 0.1]}
      rotation={[-Math.PI / 2, 0, 0]}
    >
      <meshStandardMaterial
        color="#cccccc"
        roughness={0.5}
        metalness={0.8}
        transparent={!!selectedId}
        opacity={selectedId ? 0.3 : 1}
      />
    </mesh>
  );
};

const SelectedComponent = ({ selectedId }: { selectedId: string | null }) => {
  if (!selectedId) return null;

  // Load the selected component STL
  const componentUrl = `http://localhost:8000/api/component/${selectedId}`;
  const geometry = useLoader(STLLoader, componentUrl);

  // Center geometry
  useMemo(() => {
    if (geometry) geometry.center();
  }, [geometry]);

  return (
    <mesh
      geometry={geometry}
      scale={[0.1, 0.1, 0.1]}
      rotation={[-Math.PI / 2, 0, 0]}
    >
      <meshStandardMaterial
        color="#ff6b35"
        roughness={0.5}
        metalness={0.8}
        emissive="#ff6b35"
        emissiveIntensity={0.3}
      />
    </mesh>
  );
};

export const CADViewer = ({ url, selectedId }: { url?: string, selectedId: string | null }) => {
  return (
    <Canvas shadows dpr={[1, 2]} camera={{ position: [50, 50, 50], fov: 45 }}>
      <color attach="background" args={['#1a1a1a']} />

      <Suspense fallback={null}>
        <Stage environment="city" intensity={0.5} adjustCamera>
          {url && <Model url={url} selectedId={selectedId} />}
          {selectedId && <SelectedComponent selectedId={selectedId} />}
          {!url && (
            // Placeholder Cube if no model
            <mesh>
              <boxGeometry args={[10, 10, 10]} />
              <meshStandardMaterial color="gray" wireframe />
            </mesh>
          )}
        </Stage>
      </Suspense>

      <Grid infiniteGrid fadeDistance={500} sectionColor="#444" cellColor="#222" />
      <OrbitControls makeDefault />
    </Canvas>
  );
};
