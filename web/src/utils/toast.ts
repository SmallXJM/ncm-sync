import { render, h, ref } from 'vue';
import ToastContainer from '@/components/ToastContainer.vue';

let containerVNode: any = null;

const getContainer = () => {
  if (containerVNode) return containerVNode.component.exposed;

  // 创建一个挂载点
  const el = document.createElement('div');
  document.body.appendChild(el);

  // 渲染虚拟节点
  containerVNode = h(ToastContainer);
  render(containerVNode, el);

  return containerVNode.component.exposed;
};

export const toast = {
  info: (msg: string) => getContainer().add(msg, 'info'),
  success: (msg: string) => getContainer().add(msg, 'success'),
  warning: (msg: string) => getContainer().add(msg, 'warning'),
  error: (msg: string) => getContainer().add(msg, 'error'),
  show: (msg: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => getContainer().add(msg, type),
};