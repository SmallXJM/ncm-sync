import { ref, watch } from 'vue'

const isNarrow = ref(
  localStorage.getItem('siderbar') === 'narrow'
)

const isMobileOpen = ref(false)

watch(isNarrow, (val) => {
  localStorage.setItem('siderbar', val ? 'narrow' : 'widen')
})

export function useSidebar() {
  return {
    isNarrow,
    isMobileOpen,
  }
}
