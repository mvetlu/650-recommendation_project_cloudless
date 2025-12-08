# Run in CLI once to create dynamodb tables "manually"
``` bash
# 1) rec-users
aws dynamodb create-table \
  --table-name rec-users \
  --attribute-definitions AttributeName=user_id,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# 2) rec-items
aws dynamodb create-table \
  --table-name rec-items \
  --attribute-definitions AttributeName=item_id,AttributeType=S \
  --key-schema AttributeName=item_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# 3) rec-interactions
aws dynamodb create-table \
  --table-name rec-interactions \
  --attribute-definitions \
      AttributeName=user_id,AttributeType=S \
      AttributeName=interaction_id,AttributeType=S \
  --key-schema \
      AttributeName=user_id,KeyType=HASH \
      AttributeName=interaction_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# 4) rec-recommendations
aws dynamodb create-table \
  --table-name rec-recommendations \
  --attribute-definitions AttributeName=user_id,AttributeType=S \
  --key-schema AttributeName=user_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
  ```

## to check tables were created and are active*
```bash
aws dynamodb list-tables --region us-east-1
```
## to clean up the tables when done
aws dynamodb delete-table --table-name rec-users --region us-east-1
aws dynamodb delete-table --table-name rec-items --region us-east-1
aws dynamodb delete-table --table-name rec-interactions --region us-east-1
aws dynamodb delete-table --table-name rec-recommendations --region us-east-1

