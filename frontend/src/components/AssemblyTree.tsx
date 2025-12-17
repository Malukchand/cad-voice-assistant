import React, { useState } from 'react';
import { ChevronRight, ChevronDown, Box, Layers, Shell, Triangle } from 'lucide-react';
import type { TreeNode } from '../types';

interface AssemblyTreeProps {
  data: TreeNode;
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const TreeNodeItem = ({ node, level, selectedId, onSelect }: { node: TreeNode, level: number, selectedId: string | null, onSelect: (id: string) => void }) => {
  const [expanded, setExpanded] = useState(true);
  const isSelected = selectedId === node.id;
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div>
      <div
        className={`flex items-center py-1 px-2 cursor-pointer select-none text-sm transition-colors ${isSelected ? 'bg-blue-100 text-blue-700 font-medium' : 'hover:bg-gray-100 text-gray-700'
          }`}
        style={{ paddingLeft: `${level * 12 + 4}px` }}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(node.id);
        }}
      >
        <div
          className="w-4 h-4 mr-1 flex items-center justify-center text-gray-400 hover:text-gray-600"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
        >
          {hasChildren && (
            expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />
          )}
        </div>

        {node.type === 'Assembly' ?
          <Layers size={14} className="mr-2 text-orange-500" /> :
          node.type === 'Shell' ?
          <Shell size={14} className="mr-2 text-green-500" /> :
          node.type === 'Face' ?
          <Triangle size={14} className="mr-2 text-purple-500" /> :
          <Box size={14} className="mr-2 text-blue-500" />
        }

        <span>{node.name}</span>
      </div>

      {hasChildren && expanded && (
        <div>
          {node.children.map(child => (
            <TreeNodeItem
              key={child.id}
              node={child}
              level={level + 1}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const AssemblyTree = ({ data, selectedId, onSelect }: AssemblyTreeProps) => {
  // If no data, show placeholder
  if (!data) return <div className="p-4 text-gray-400 text-sm">No model loaded.</div>;

  return (
    <div className="flex flex-col">
      <TreeNodeItem node={data} level={0} selectedId={selectedId} onSelect={onSelect} />
    </div>
  );
};
