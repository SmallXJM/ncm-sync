<template>
  <div v-if="totalPages > 1" class="pagination">
    <div class="btn-group">
      <!-- First Page -->
      <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === 1" @click="handlePageChange(1)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
          stroke-linejoin="round">
          <polyline points="11 17 6 12 11 7"></polyline>
          <polyline points="18 17 13 12 18 7"></polyline>
        </svg>
      </button>

      <!-- Previous Page -->
      <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === 1"
        @click="handlePageChange(currentPage - 1)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
          stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"></polyline>
        </svg>
      </button>

      <!-- Page Numbers -->
      <template v-for="page in visiblePages" :key="page">
        <span v-if="page === '...'" class="pagination-ellipsis">...</span>
        <button v-else class="btn btn-sm" :class="currentPage === page ? 'btn-primary' : 'btn-secondary'"
          @click="handlePageChange(Number(page))">
          {{ page }}
        </button>
      </template>

      <!-- Next Page -->
      <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === totalPages"
        @click="handlePageChange(currentPage + 1)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
          stroke-linejoin="round">
          <polyline points="9 18 15 12 9 6"></polyline>
        </svg>
      </button>

      <!-- Last Page -->
      <button class="btn btn-secondary btn-sm icon-btn" :disabled="currentPage === totalPages"
        @click="handlePageChange(totalPages)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
          stroke-linejoin="round">
          <polyline points="13 17 18 12 13 7"></polyline>
          <polyline points="6 17 11 12 6 7"></polyline>
        </svg>
      </button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

const props = defineProps({
  totalItems: {
    type: Number,
    required: true
  },
  currentPage: {
    type: Number,
    required: true
  },
  pageSize: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['page-change'])

const totalPages = computed(() => Math.ceil(props.totalItems / props.pageSize))

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = props.currentPage
  const windowSize = 5

  // 总页数不够 5，全部显示
  if (total <= windowSize) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  let start = current - Math.floor(windowSize / 2)
  let end = current + Math.floor(windowSize / 2)

  // 左边越界
  if (start < 1) {
    start = 1
    end = windowSize
  }

  // 右边越界
  if (end > total) {
    end = total
    start = total - windowSize + 1
  }

  const pages = []

  // 左边省略号
  if (start > 1) {
    pages.push("...")   // 省略
  }

  // 中间页码
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  // 右边省略号
  if (end < total) {
    pages.push("...")   // 省略
  }

  return pages
})

const handlePageChange = (page: number) => {
  if (page < 1 || page > totalPages.value || page === props.currentPage) return
  emit('page-change', page)
}
</script>

<style scoped lang="scss">
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: var(--spacing-lg);
}

.btn-group {
  display: flex;
  gap: var(--spacing-sm);

  .btn {
    width: 36px;
    height: 36px;
  }

  .icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0;
  }

  .icon-btn svg {
    width: 16px;
    height: 16px;
    stroke-width: 2.5px;
  }
}

.pagination-ellipsis {
  padding: 0 0.5rem;
  color: var(--text-muted);
  line-height: 2;
}
</style>
