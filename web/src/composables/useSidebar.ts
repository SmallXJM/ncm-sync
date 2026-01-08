import { ref, watch } from 'vue'

const isNarrow = ref(
  localStorage.getItem('siderbar') === 'narrow'
)

watch(isNarrow, (val) => {
  localStorage.setItem('siderbar', val ? 'narrow' : 'widen')
})

export function useSidebar() {
  return {
    isNarrow
  }
}
