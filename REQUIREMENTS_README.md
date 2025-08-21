# 📦 Requirements Organization

This project is organized into modular requirements files for better dependency management and flexibility.

## 🏗️ **Module Structure**

### **1. Core Backend (`backend-django/requirements.txt`)**
Essential Django dependencies for the main application:
- Django Framework & REST API
- Authentication (JWT)
- CORS handling
- Environment configuration
- Basic HTTP requests

**Install only core:**
```bash
cd backend-django
pip install -r requirements.txt
```

### **2. Government Data (`gov/requirements.txt`)**
Modules for government data collection:
- **Nadlan**: Real estate transactions
- **Decisive Appraisal**: Government appraisals
- Web scraping & PDF processing
- Data validation & caching

**Install government modules:**
```bash
cd gov
pip install -r requirements.txt
```

### **3. GIS Module (`gis/requirements.txt`)**
Geographic Information System capabilities:
- Spatial data processing
- Coordinate transformations
- Map data analysis
- Privilege page processing

**Install GIS module:**
```bash
cd gis
pip install -r requirements.txt
```

### **4. Yad2 Real Estate (`yad2/requirements.txt`)**
Real estate listing management:
- Web scraping from Yad2
- Property data collection
- Scheduling & automation
- Rate limiting & caching

**Install Yad2 module:**
```bash
cd yad2
pip install -r requirements.txt
```

### **5. RAMI Module (`rami/requirements.txt`)**
Real estate appraisal data:
- PDF document processing
- Appraisal data extraction
- Data validation
- Caching mechanisms

**Install RAMI module:**
```bash
cd rami
pip install -r requirements.txt
```

## 🚀 **Installation Options**

### **Option 1: Core Backend Only**
```bash
./install-core.sh
```
Perfect for basic Django development without external data sources.

### **Option 2: Complete Installation**
```bash
./install-all.sh
```
Installs all modules for full functionality.

### **Option 3: Manual Module Installation**
```bash
# Install specific modules as needed
pip install -r gov/requirements.txt
pip install -r gis/requirements.txt
pip install -r yad2/requirements.txt
pip install -r rami/requirements.txt
```

## 🔧 **Development Workflow**

### **Starting with Core Only**
1. Install core backend: `./install-core.sh`
2. Run Django server: `cd backend-django && python3 manage.py runserver`
3. Add modules as needed for specific features

### **Adding Modules Incrementally**
```bash
# Need government data?
pip install -r gov/requirements.txt

# Need GIS capabilities?
pip install -r gis/requirements.txt

# Need real estate listings?
pip install -r yad2/requirements.txt
```

## 📊 **Dependency Categories**

### **Core Dependencies** (Always Required)
- Django & REST framework
- Basic HTTP requests
- Environment configuration

### **Data Processing** (Most Modules)
- pandas, numpy
- Data validation (pydantic, marshmallow)
- Caching (redis)

### **Web Scraping** (gov, yad2, rami)
- beautifulsoup4, lxml
- selenium, webdriver-manager
- Rate limiting

### **GIS Processing** (gis only)
- geopandas, shapely
- pyproj, rasterio
- Spatial data handling

### **PDF Processing** (gov, gis, rami)
- PyPDF2, pdfplumber
- PyMuPDF (rami only)

## 🎯 **Use Cases**

### **Basic Real Estate App**
```bash
./install-core.sh
pip install -r yad2/requirements.txt
```

### **Government Data Analysis**
```bash
./install-core.sh
pip install -r gov/requirements.txt
```

### **Full GIS Real Estate Platform**
```bash
./install-all.sh
```

## ⚠️ **Important Notes**

1. **Core backend must be installed first**
2. **Modules can be installed independently**
3. **Some modules have overlapping dependencies** (will be deduplicated by pip)
4. **Redis is required for caching** in most modules
5. **Check individual module READMEs** for specific configuration

## 🔍 **Troubleshooting**

### **Common Issues**
- **Module not found**: Check if requirements.txt exists in module directory
- **Import errors**: Ensure module is installed: `pip install -r module/requirements.txt`
- **Version conflicts**: Use `pip check` to identify conflicts

### **Clean Installation**
```bash
# Remove all packages and reinstall
pip uninstall -r <(pip freeze) -y
./install-core.sh
```

## 📚 **Next Steps**

1. **Choose your installation path** (core vs. complete)
2. **Run the appropriate script**
3. **Check module-specific documentation**
4. **Configure environment variables**
5. **Start developing!**

---

**Happy coding! 🚀**
