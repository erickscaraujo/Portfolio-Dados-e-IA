# Segmentação de Clientes (RFM)

Clusterização não supervisionada com K-Means sobre métricas RFM.

## Destaques
- Método do cotovelo + coeficiente de silhueta para escolher o k
- Perfil dos centroides invertido para valores de negócio
- Nomeação automática de personas (VIP, Fiéis, Promissores, Hibernando)
- Dispersão PCA 2D e base final `outputs/segmentos.csv`

## Stack
pandas, numpy, scikit-learn, matplotlib

## Como rodar
```bash
python main.py
```
