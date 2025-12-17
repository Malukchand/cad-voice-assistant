import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AssemblyTree } from './components/AssemblyTree';
import { CADViewer } from './components/CADViewer';
import { MenuBar } from './components/MenuBar';
import { VoicePanel } from './components/VoicePanel';
import { HasseDiagram } from './components/HasseDiagram';
import { Move3d, Upload, Box } from 'lucide-react';
import type { TreeNode } from './types';

const API_BASE = "http://localhost:8000";

export default function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [treeData, setTreeData] = useState<TreeNode | null>(null);
  const [modelUrl, setModelUrl] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [lastMessage, setLastMessage] = useState<string>("");
  const [showHasse, setShowHasse] = useState(false);

  // Initial Mock Data
  useEffect(() => {
    setTreeData({
      id: "root", name: "Robot-EBOM", type: "Assembly",
      children: [
        {
          id: "1", name: "Arm-Assembly", type: "Assembly", children: [
            { id: "1-1", name: "Upper-arm", type: "Part", children: [] },
            { id: "1-2", name: "Lower-arm", type: "Part", children: [] },
          ]
        },
        { id: "2", name: "Base-Assembly", type: "Assembly", children: [] }
      ]
    });
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/upload`, formData);
      if (res.data.status === "success") {
        setTreeData(res.data.tree);
        setModelUrl(`${API_BASE}/api/model.stl?t=${Date.now()}`); // Force re-fetch
        setLastMessage("File uploaded.");
      }
    } catch (err) {
      console.error("Upload failed", err);
      alert("Failed to upload model");
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceData = (data: any) => {
    // Show transcription/response
    if (data.transcription) {
      setLastMessage(`You: "${data.transcription}"\nAI: "${data.response}"`);
    }

    // If model modified, refresh view
    if (data.modified) {
      console.log("Model modified, refreshing...");
      setModelUrl(`${API_BASE}/api/model.stl?t=${Date.now()}`); // Force re-fetch
      if (data.tree) {
        setTreeData(data.tree);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100 font-sans text-gray-900">
      <MenuBar onShowHasse={() => setShowHasse(true)} />

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Assembly Tree */}
        <div className="w-80 bg-white border-r border-gray-300 flex flex-col shadow-sm z-10">
          <div className="p-3 bg-gray-100 border-b font-semibold text-sm text-gray-700 flex justify-between items-center">
            <span>Assembly Tree</span>
            <label className="cursor-pointer bg-blue-500 hover:bg-blue-600 text-white p-1 rounded transition flex items-center gap-1 px-2">
              <Upload size={14} />
              <span className="text-xs">Import</span>
              <input type="file" className="hidden" accept=".stp,.step" onChange={handleFileUpload} />
            </label>
          </div>

          <div className="flex-1 overflow-auto p-2">
            {loading ? (
              <div className="p-4 text-center text-gray-500 animate-pulse">Loading model...</div>
            ) : (
              <AssemblyTree data={treeData!} selectedId={selectedId} onSelect={setSelectedId} />
            )}
          </div>

          <div className="p-4 border-t bg-gray-50 flex flex-col gap-2">
            {/* Bottom Left Controls */}
            <div className="text-[10px] uppercase text-gray-400 font-bold tracking-wider">Messages</div>
            <div className="h-20 bg-white border rounded p-2 text-xs text-gray-500 overflow-y-auto mb-2 shadow-inner whitespace-pre-wrap">
              {lastMessage || (selectedId ? `Selected node: ${selectedId}` : "System Ready.")}
            </div>

            <div className="flex items-center justify-between mt-2">
              <div className="flex flex-col items-center gap-1">
                <button
                  className="p-2 bg-gray-200 rounded hover:bg-gray-300 text-gray-700 transition"
                  onClick={() => setSelectedId(null)}
                  title="Reset Selection"
                >
                  <Move3d size={18} />
                </button>
                <span className="text-[10px] text-gray-500">Reset</span>
              </div>
              <VoicePanel onCommandProcessed={handleVoiceData} />
            </div>
          </div>
        </div>

        {/* Center Panel: 3D Viewer */}
        <div className="flex-1 relative bg-gradient-to-br from-gray-200 to-gray-400 overflow-hidden">
          <div className="absolute top-4 right-4 z-10 bg-white/90 px-3 py-1 rounded-full text-xs font-medium shadow-sm border flex items-center gap-2">
            <Box size={12} className="text-blue-500" /> Interactive 3D View
          </div>
          <div className="w-full h-full">
            <CADViewer url={modelUrl} selectedId={selectedId} />
          </div>
        </div>
      </div>

      {/* Hasse Diagram Modal */}
      {showHasse && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowHasse(false)}>
          <div className="bg-white p-4 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4 border-b pb-2">
              <h2 className="text-xl font-bold text-gray-800">Assembly Hasse Diagram</h2>
              <button onClick={() => setShowHasse(false)} className="text-gray-500 hover:text-gray-700 text-2xl leading-none">&times;</button>
            </div>
            <div className="flex-1 overflow-auto flex justify-center bg-gray-50 border rounded p-4 relative">
              <HasseDiagram
                apiBase={API_BASE}
                onNodeClick={(id) => {
                  setSelectedId(id);
                  // Optional: close modal? Or keep open? User request implies interactive highlighting.
                  // "Selecting a node highlights: Related parts in the 3D CAD view"
                  // Keeping it open allows exploring.
                }}
              />
            </div>
            <div className="mt-4 flex justify-end">
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                onClick={() => setShowHasse(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
