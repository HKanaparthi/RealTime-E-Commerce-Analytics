# ShopStream Frontend Dockerfile

FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install


COPY . .

# Expose port
EXPOSE 5173

# Default command (development)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
