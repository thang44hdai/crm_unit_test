<template>
  <div class="flex items-center justify-center w-8 h-8 bg-gray-100 cursor-pointer rounded-xl hover:bg-gray-200"
    :class="{ 'ring-2 ring-blue-500': selected }">
    <img :src="logo" class="w-4 h-4" />
  </div>
  <p v-if="serviceName" class="text-xs text-center text-gray-700">
    {{ serviceName }}
  </p>
</template>

<script setup>

defineProps({
  logo: {
    type: String,
    required: true
  },
  serviceName: {
    type: String,
    default: ''
  },
  selected: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped></style>
