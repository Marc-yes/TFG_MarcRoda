# Estadi 1: Compilació de recursos estàtics (CSS, JS) amb Node
FROM node:18-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Estadi 2: Servidor PHP + Apache per a producció local (on-premises)
FROM php:8.2-apache

# Instal·lem dependències del sistema i extensions de PHP requerides per Laravel i SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    unzip \
    libzip-dev \
    libsqlite3-dev \
    && docker-php-ext-install zip pdo_sqlite \
    && rm -rf /var/lib/apt/lists/*

# Activem el mòdul de reescriptura (rewrite) d'Apache
RUN a2enmod rewrite

# Configurem el DocumentRoot d'Apache perquè apunti a la carpeta public de Laravel
ENV APACHE_DOCUMENT_ROOT=/var/www/html/public
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/sites-available/*.conf
RUN sed -ri -e 's!/var/www/html!${APACHE_DOCUMENT_ROOT}!g' /etc/apache2/apache2.conf /etc/apache2/conf-available/*.conf

# Instal·lem Composer globalment des de la seva imatge oficial
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Copiem el codi del projecte
COPY . .

# Copiem els fitxers compilats a l'estadi de Node
COPY --from=frontend-builder /app/public/build ./public/build

# Instal·lem les dependències de composer (només de producció) i optimitzem el carregador
RUN composer install --no-dev --optimize-autoloader

# Donem els permisos de persistència de storage i bootstrap a l'usuari d'Apache (www-data)
RUN chown -R www-data:www-data storage bootstrap/cache

EXPOSE 80

CMD ["apache2-foreground"]
