import { render, h, type VNode, type Component } from 'vue';
import ToastContainer from '@/components/AppToastContainer.vue';


interface ToastContainerExposed {
  add: (message: string, title?: string, type?: 'info' | 'success' | 'warning' | 'error', duration?: number, icon?: Component) => void;
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

type ToastType = 'info' | 'success' | 'warning' | 'error';

// 核心 show 方法
const show = (options: { type?: ToastType, message: string, title?: string, icon?: Component, duration?: number }) => {
  const { type = 'info', message, title = '', icon, duration = 5000 } = options;
  return getContainer().add(title, message, type, duration, icon);
};

// 导出对象
export const toast = {
  show,
  // 简写：直接通过 show 实现
  info: (msg: string, title: string = '', icon?: Component) => show({ type: 'info', message: msg, title, icon }),
  success: (msg: string, title: string = '', icon?: Component) => show({ type: 'success', message: msg, title, icon }),
  warning: (msg: string, title: string = '', icon?: Component) => show({ type: 'warning', message: msg, title, icon }),
  error: (msg: string, title: string = '', icon?: Component) => show({ type: 'error', message: msg, title, icon }), 
};
