#!/bin/bash

GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear
echo -e "${BLUE}==================================================${NC}"
echo -e "${CYAN}    🛡️  SAFE CONTACT (БЕЗОПАСНЫЙ КОНТАКТ)${NC}"
echo -e "${BLUE}==================================================${NC}"
echo -e "Среда разработки успешно развернута."
echo ""
echo -e "${YELLOW}📦 ЗАВИСИМОСТИ:${NC}"
echo -e "  - Node.js модули установлены в /frontend"
echo -e "  - Python пакеты установлены в venv контейнера"
echo ""
echo -e "${YELLOW}🚀 КОМАНДЫ ДЛЯ ЗАПУСКА:${NC}"
echo -e "  ${GREEN}npm run dev --prefix frontend${NC}  -> Запустить фронт"
echo -e "  ${GREEN}python backend/wsgi.py${NC}         -> Запустить бэк"
echo ""
echo -e "${YELLOW}📖 ДОКУМЕНТАЦИЯ:${NC}"
echo -e "  Посмотри ${BLUE}/docs/DATABASE_REQUIREMENTS.md${NC} перед правкой моделей."
echo ""
echo -e "${BLUE}==================================================${NC}"
echo -e "Приятной разработки! По любым вопросам — к Лиду."