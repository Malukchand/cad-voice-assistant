import React from 'react';
import { Menu, FileBox, Settings, HelpCircle, Box } from 'lucide-react';

interface MenuBarProps {
  onShowHasse?: () => void;
}

export const MenuBar = ({ onShowHasse }: MenuBarProps) => {
  return (
    <div className="bg-gray-800 text-white flex items-center px-4 py-2 text-sm shadow-md">
      <div className="font-bold mr-6 text-blue-400 flex items-center gap-2">
        <Box size={18} /> CAD Assistant
      </div>
      <div className="flex gap-6">
        <div className="cursor-pointer hover:text-gray-300 flex items-center gap-1"><FileBox size={14} /> File</div>
        <div className="cursor-pointer hover:text-gray-300 flex items-center gap-1"><Menu size={14} /> View</div>
        <div
          className="cursor-pointer hover:text-gray-300 flex items-center gap-1"
          onClick={onShowHasse}
          title="Show Hasse Diagram"
        >
          <Settings size={14} /> Tools (Hasse)
        </div>
        <div className="cursor-pointer hover:text-gray-300 flex items-center gap-1"><HelpCircle size={14} /> Help</div>
      </div>
    </div>
  );
};
