FROM node:22-alpine

WORKDIR /app

# Cài dependency ở layer riêng: đổi source không phải npm install lại.
COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
