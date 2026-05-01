<script setup>
import { apiGetUserRole } from '@/services/specialists.api'
import { Button } from 'primevue'
import { ref } from 'vue'

const userRole = ref(null)

const handleFetchRole = async () => {
  userRole.value = null

  try {
    const data = await apiGetUserRole()
    userRole.value = data.role
  } catch (e) {
    console.error(e)
  }
}
</script>

<template>
  <Button label="пыпы" @click="handleFetchRole" />
  <div v-if="userRole" class="mt-4">
    <p>
      Твоя роль: <strong>{{ userRole }}</strong>
    </p>
  </div>
</template>
