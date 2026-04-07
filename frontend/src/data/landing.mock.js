export const stepsData = {
  client: [
    {
      id: 1,
      icon: 'pi pi-search',
      title: 'Найдите психолога',
      desc: 'Используйте фильтры по темам и стоимости.',
    },
    {
      id: 2,
      icon: 'pi pi-calendar',
      title: 'Выберите время',
      desc: 'Запишитесь в календарь в пару кликов.',
    },
    {
      id: 3,
      icon: 'pi pi-video',
      title: 'Начните сессию',
      desc: 'Встречайтесь в нашем чате прямо в браузере.',
    },
  ],
  specialist: [
    {
      id: 1,
      icon: 'pi pi-user-plus',
      title: 'Регистрация',
      desc: 'Заполните анкету и загрузите свои дипломы.',
    },
    {
      id: 2,
      icon: 'pi pi-pen-to-square',
      title: 'Проверка',
      desc: 'Мы подтвердим ваш профиль в течение суток.',
    },
    {
      id: 3,
      icon: 'pi pi-desktop',
      title: 'Работа',
      desc: 'Принимайте записи и помогайте клиентам.',
    },
  ],
}

export const specialistsData = [
  {
    id: 1,
    avatarUrl:
      'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Felis_silvestris_silvestris.jpg/330px-Felis_silvestris_silvestris.jpg',
    displayName: 'Анна Петрова',
    specialization: 'Семейная терапия',
    rating: 4.9,
    minPrice: 2500,
    isOnline: true,
  },
  {
    id: 2,
    avatarUrl:
      'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTPRbAPPW_QVO9CeKIh9NAOe-s6NEpkJZIPlQ&s',
    displayName: 'Михаил Соколов',
    specialization: 'Творожные расстройства',
    rating: 4.8,
    minPrice: 3000,
    isOnline: true,
  },
  {
    id: 3,
    avatarUrl:
      'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTI0GH9NxaVe4RVmhhsY11WWhcsYA8go1hwyA&s',
    displayName: 'Елена Волкова',
    specialization: 'Депрессия и стресс',
    rating: 4.7,
    minPrice: 2800,
    isOnline: true,
  },
  {
    id: 4,
    avatarUrl:
      'https://storage-api.petstory.ru/resize/1000x1000x80/1b/15/eb/1b15ebf4227346c2a1d74e5b5cf69d79.jpeg',
    displayName: 'Дарья Тимофеева',
    specialization: 'Отношения',
    rating: 4.5,
    minPrice: 2300,
    isOnline: false,
  },
  {
    id: 5,
    avatarUrl:
      'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQc_JuBqqylPknXrkelsPsPtS7SzoY1RBmQ1A&s',
    displayName: 'Даниил Орлов',
    specialization: 'Самооценка',
    rating: 4.5,
    minPrice: 3100,
    isOnline: true,
  },
]

export const benefitsData = {
  client: [
    {
      id: 1,
      icon: 'pi pi-clock',
      title: 'Удобство',
      desc: 'Консультации в любое удобное время из любого время',
    },
    {
      id: 2,
      icon: 'pi pi-verified',
      title: 'Проверенные специалисты',
      desc: 'Все психологи прошли тщательную проверку и имеют соответсвующее образование',
    },
    {
      id: 3,
      icon: 'pi pi-shield',
      title: 'Конфиденциальность',
      desc: 'Полная анонимность и защита персональных данных',
    },
    {
      id: 4,
      icon: 'pi pi-dollar',
      title: 'Доступные цены',
      desc: 'Справедливые цены без переплат за аренду кабинета',
    },
  ],
  specialist: [
    {
      id: 1,
      icon: 'pi pi-calendar',
      title: 'Гибкий график',
      desc: 'Работайте в удобное для Вас время и планируйте свой график',
    },
    {
      id: 2,
      icon: 'pi pi-chart-line',
      title: 'Расширение клиентской базы',
      desc: 'Получайте больше клиентов благодаря нашей платформе',
    },
    {
      id: 3,
      icon: 'pi pi-home',
      title: 'Без аренды кабинета',
      desc: 'Экономьте на аренде офиса и работайте из дома',
    },
    {
      id: 4,
      icon: 'pi pi-users',
      title: 'Профессиональное сообщество',
      desc: 'Общайтесь с коллегами и развивайтесь профессионально',
    },
  ],
}

export const reviewsData = [
  {
    quote:
      'Очень удобно получать помощь психолога, не выходя из дома. Мой специалист помог мне справиться с тревожностью.',
    author: 'Мария К.',
    stars: '5',
    role: 'client',
  },
  {
    quote:
      'Платформа помогла мне найти отличного семейного психолога. Теперь наши отношения стали намного лучше.',
    author: 'Алексей П.',
    stars: '5',
    role: 'client',
  },
  {
    quote:
      'Как психолог, я очень довольна работой на этой платформе. Удобный интерфейс и постоянный поток клиентов.',
    author: 'Елена В.',
    stars: '5',
    role: 'specialist',
  },
]

export const faqData = [
  { value: '1', title: 'Как проходят онлайн-консультации?', content: '. . .' },
  { value: '2', title: 'Как выбрать подходящего психолога?', content: '. . .' },
  { value: '3', title: 'Безопасны ли мои данные?', content: '. . .' },
  { value: '4', title: 'Как стать психологом на платформе?', content: '. . .' },
]
