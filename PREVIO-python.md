## 1- conectar a la instancia

```bash
curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

```

````bash Miniconda3-latest-Linux-x86_64.sh````

- `Proceed with initialization? [yes|no]
[no] >>> yes`


`source ~/.bashrc`


### 1.2 ambiente virtual

```bash
conda create --name vector python=3.12


conda activate vector
```

instalar requerimientos

`pip install -r requirements.txt`