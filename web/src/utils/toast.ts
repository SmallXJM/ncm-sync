import { render, h, type VNode } from 'vue';
import ToastContainer from '@/components/AppToastContainer.vue';


interface ToastContainerExposed {
  add: (title: string, message: string, type: 'info' | 'success' | 'warning' | 'error', duration?: number) => void;
}

let containerVNode: VNode | null = null;

const getContainer = (): ToastContainerExposed => {
  // 如果已存在，直接从 component.exposed 获取
  if (containerVNode?.component?.exposed) {
    return containerVNode.component.exposed as ToastContainerExposed;
  }

  // 创建一个挂载点
  const el = document.createElement('div');
  el.id = 'app-toast-root';
  document.body.appendChild(el);

  // 渲染虚拟节点
  containerVNode = h(ToastContainer);
  render(containerVNode, el);

  // 获取暴露的方法
  const exposed = containerVNode.component?.exposed as ToastContainerExposed;

  if (!exposed) {
    throw new Error('Toast 容器初始化失败：请检查 AppToastContainer 是否使用了 defineExpose');
  }

  return exposed;
};

export const toast = {
  info: (title: string, msg: string) => getContainer().add(title, msg, 'info'),
  success: (title: string, msg: string) => getContainer().add(title, msg, 'success'),
  warning: (title: string, msg: string) => getContainer().add(title, msg, 'warning'),
  error: (title: string, msg: string) => getContainer().add(title, msg, 'error'),
  show: (title: string, msg: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => getContainer().add(title, msg, type),
};