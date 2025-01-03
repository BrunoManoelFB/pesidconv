# Usar a imagem base do Python
FROM python:3.10-slim

# Configurar o diretório de trabalho
WORKDIR /app

# Copiar os arquivos necessários para a aplicação
COPY . .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expor a porta em que a aplicação Flask será executada
EXPOSE 5000

# Comando padrão para iniciar a aplicação
CMD ["python", "app.py"]
