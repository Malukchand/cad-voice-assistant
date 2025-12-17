// src/types.ts
export interface TreeNode {
  id: string;
  name: string;
  type: 'Assembly' | 'Part' | 'Shell' | 'Face';
  children: TreeNode[];
}
