<script setup>
import { faqData } from '@/data/landing.mock'
import { AccordionContent, Accordion, AccordionHeader, AccordionPanel } from 'primevue'
</script>

<template>
  <section class="max-w-3xl mx-auto w-full flex flex-col gap-8">
    <h2>FAQ</h2>
    <Accordion :value="['1']" multiple>
      <AccordionPanel
        v-for="faq in faqData"
        :key="faq.value"
        :value="faq.value"
        class="border-b border-zinc-200 dark:border-zinc-800"
      >
        <AccordionHeader class="py-4 text-xl font-medium">{{ faq.title }}</AccordionHeader>
        <AccordionContent>
          <p class="text-zinc-600 dark:text-zinc-400 pb-4">{{ faq.content }}</p>
        </AccordionContent>
      </AccordionPanel>
    </Accordion>
  </section>
</template>
