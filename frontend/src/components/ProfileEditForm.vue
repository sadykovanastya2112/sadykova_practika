<script setup>
import { ref, inject, onMounted, computed } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import IftaLabel from 'primevue/iftalabel'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import Button from 'primevue/button'
import Message from 'primevue/message'
import { apiDeleteUser, apiGetUserProfile, apiUpdateProfile } from '@/services/api.js'
import { authState } from '@/services/auth.js'

const dialogRef = inject('dialogRef')
const confirm = useConfirm()

const loading = ref(true)
const isEditing = ref(false)

const profileData = ref({})
const originalData = ref({})
const role = computed(() => authState.role)

onMounted(async () => {
  try {
    const data = await apiGetUserProfile()
    profileData.value = { ...data }
    originalData.value = { ...data }
  } finally {
    loading.value = false
  }
})

const startEdit = () => {
  isEditing.value = true
}

const cancelEdit = () => {
  profileData.value = { ...originalData.value }
  isEditing.value = false
}

const handleSave = async () => {
  if (role.value === 'client') {
    await submitChanges()
  } else {
    confirm.require({
      message:
        'Предыдущие данные не сохранятся, профиль потеряет верификацию и будет отправлена заявка на модерацию. Продолжить?',
      header: 'Подтверждение',
      icon: 'pi pi-exclamation-triangle',
      accept: async () => {
        await submitChanges()
      },
    })
  }
}

const submitChanges = async () => {
  // Формируем объект для отправки согласно спецификации API
  let payload
  if (role.value === 'client') {
    payload = {
      display_name: profileData.value.display_name,
      bio: profileData.value.bio,
      avatar_url: profileData.value.photo_url, // Уточните поле, в GET было photo_url или avatar_url? В API на запись avatar_url
    }
  } else {
    payload = {
      specialization: profileData.value.specialization,
      bio: profileData.value.bio,
      base_price: profileData.value.base_price,
      photo_url: profileData.value.photo_url,
      experience_years: profileData.value.experience_years,
      first_name: profileData.value.first_name,
      last_name: profileData.value.last_name,
      education: profileData.value.education,
    }
  }

  await apiUpdateProfile(payload)
  isEditing.value = false
  originalData.value = { ...profileData.value }

  dialogRef.value.close()
}

const handleDeleteAccount = () => {
  confirm.require({
    message: 'Удалить аккаунт навсегда?',
    accept: async () => {
      await apiDeleteUser()
      dialogRef.value.close() // Закрываем диалог сразу после удаления
    },
  })
}
</script>

<template>
  <div v-if="loading" class="p-4 text-center">Загрузка...</div>
  <div v-else class="flex flex-col gap-4 p-2">
    <!-- Статус для специалиста -->
    <Message v-if="role === 'specialist'" severity="info" :closable="false">
      <div><strong>Статус:</strong> {{ profileData.verification_status }}</div>
      <div v-if="profileData.reject_reason" class="mt-1 text-red-500">
        <strong>Причина отказа:</strong> {{ profileData.reject_reason }}
      </div>
    </Message>

    <!-- Почта (Readonly) -->
    <IftaLabel>
      <InputText id="email" v-model="profileData.email" disabled class="w-full" />
      <label for="email">Почта (аккаунт)</label>
    </IftaLabel>

    <!-- Поля КЛИЕНТА -->
    <template v-if="role === 'client'">
      <IftaLabel>
        <InputText
          id="dn"
          v-model="profileData.display_name"
          :disabled="!isEditing"
          maxlength="64"
          class="w-full"
        />
        <label for="dn">Отображаемое имя</label>
      </IftaLabel>

      <IftaLabel>
        <Textarea
          id="bio"
          v-model="profileData.bio"
          :disabled="!isEditing"
          rows="3"
          class="w-full"
          style="resize: none"
        />
        <label for="bio">Описание</label>
      </IftaLabel>
    </template>

    <!-- Поля СПЕЦИАЛИСТА -->
    <template v-else>
      <div class="flex gap-2">
        <IftaLabel class="w-full">
          <InputText
            id="fn"
            v-model="profileData.first_name"
            :disabled="!isEditing"
            maxlength="32"
            class="w-full"
          />
          <label for="fn">Имя</label>
        </IftaLabel>
        <IftaLabel class="w-full">
          <InputText
            id="ln"
            v-model="profileData.last_name"
            :disabled="!isEditing"
            maxlength="32"
            class="w-full"
          />
          <label for="ln">Фамилия</label>
        </IftaLabel>
      </div>

      <IftaLabel>
        <InputText
          id="spec"
          v-model="profileData.specialization"
          :disabled="!isEditing"
          maxlength="64"
          class="w-full"
        />
        <label for="spec">Специализация</label>
      </IftaLabel>

      <IftaLabel>
        <InputText
          id="edu"
          v-model="profileData.education"
          :disabled="!isEditing"
          maxlength="255"
          class="w-full"
        />
        <label for="edu">Образование</label>
      </IftaLabel>

      <div class="flex gap-2">
        <IftaLabel class="w-full">
          <InputNumber
            id="exp"
            v-model="profileData.experience_years"
            :disabled="!isEditing"
            class="w-full"
          />
          <label for="exp">Стаж (лет)</label>
        </IftaLabel>
        <IftaLabel class="w-full">
          <InputNumber
            id="price"
            v-model="profileData.base_price"
            :disabled="!isEditing"
            mode="currency"
            currency="USD"
            class="w-full"
          />
          <label for="price">Стартовая цена</label>
        </IftaLabel>
      </div>

      <IftaLabel>
        <Textarea
          id="bio_spec"
          v-model="profileData.bio"
          :disabled="!isEditing"
          rows="3"
          class="w-full"
          style="resize: none"
        />
        <label for="bio_spec">Описание</label>
      </IftaLabel>
    </template>

    <!-- Ссылка на аватар (общая) -->
    <IftaLabel>
      <InputText id="photo" v-model="profileData.photo_url" :disabled="!isEditing" class="w-full" />
      <label for="photo">Ссылка на фото/аватар</label>
    </IftaLabel>

    <!-- Кнопки управления -->
    <div class="flex flex-col gap-2 mt-2 grow">
      <template v-if="!isEditing">
        <Button label="Редактировать" icon="pi pi-pencil" @click="startEdit" />
        <Button
          severity="danger"
          label="Удалить аккаунт"
          icon="pi pi-trash"
          @click="handleDeleteAccount"
        />
      </template>

      <template v-else>
        <Button
          label="Подтвердить"
          icon="pi pi-check"
          severity="success"
          @click="handleSave"
          class="flex-grow-1"
        />
        <Button label="Отменить" icon="pi pi-times" severity="secondary" @click="cancelEdit" />
      </template>
    </div>
  </div>
</template>
