# 필요한 패키지 불러오기
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# 워킹 디렉토리 설정
import os
cwd=os.getcwd()
parent_dir = os.path.dirname(cwd)
os.chdir(parent_dir)

## 필요한 데이터 불러오기
house_train=pd.read_csv("C:/Users/USER/Documents/LS빅데이터스쿨/LSbigdata-project1/houseprice/data/train.csv")
house_test=pd.read_csv("C:/Users/USER/Documents/LS빅데이터스쿨/LSbigdata-project1/houseprice/data/test.csv")
sub_df=pd.read_csv("C:/Users/USER/Documents/LS빅데이터스쿨/LSbigdata-project1/houseprice/data/sample_submission.csv")


## NaN 채우기
# 각 숫치형 변수는 평균 채우기
# 각 범주형 변수는 Unknown 채우기
house_train.isna().sum()
house_test.isna().sum()

## 숫자형 채우기
quantitative = house_train.select_dtypes(include = [int, float])
quantitative.isna().sum()
quant_selected = quantitative.columns[quantitative.isna().sum() > 0]

for col in quant_selected:
    house_train[col].fillna(house_train[col].mean(), inplace=True)
house_train[quant_selected].isna().sum()

## 범주형 채우기
qualitative = house_train.select_dtypes(include = [object])
qualitative.isna().sum()
qual_selected = qualitative.columns[qualitative.isna().sum() > 0]

for col in qual_selected:
    house_train[col].fillna("unknown", inplace=True)
house_train[qual_selected].isna().sum()


# test 데이터 채우기
## 숫자형 채우기
quantitative = house_test.select_dtypes(include = [int, float])
quantitative.isna().sum()
quant_selected = quantitative.columns[quantitative.isna().sum() > 0]

for col in quant_selected:
    house_test[col].fillna(house_train[col].mean(), inplace=True)
house_test[quant_selected].isna().sum()

## 범주형 채우기
qualitative = house_test.select_dtypes(include = [object])
qualitative.isna().sum()
qual_selected = qualitative.columns[qualitative.isna().sum() > 0]

for col in qual_selected:
    house_test[col].fillna("unknown", inplace=True)
house_test[qual_selected].isna().sum()


house_train.shape
house_test.shape
train_n=len(house_train)

# 통합 df 만들기 + 더미코딩
# house_test.select_dtypes(include=[int, float])

df = pd.concat([house_train, house_test], ignore_index=True)
# df.info()
df = pd.get_dummies(
    df,
    columns= df.select_dtypes(include=[object]).columns,
    drop_first=True
    )
df

# train / test 데이터셋
train_df=df.iloc[:train_n,]
test_df=df.iloc[train_n:,]

## 이상치 탐색
train_df=train_df.query("GrLivArea <= 4500")

## train
train_x=train_df.drop("SalePrice", axis=1)
train_y=train_df["SalePrice"]

## test
test_x=test_df.drop("SalePrice", axis=1)

from sklearn.linear_model import ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV

eln_model= ElasticNet()
rf_model= RandomForestRegressor(n_estimators=100)

# 그리드 서치 for ElasticNet # 릿지+라쏘, 하이퍼 파라미터를 뭐로 쓰는게 좋은지 몰라서 그리드서치
param_grid={
    'alpha': [0.1, 1.0, 10.0, 100.0],
    'l1_ratio': [0, 0.1, 0.5, 1.0]
} # 하이퍼파라미터: 모델 성능에 영향을 미침. (미리 설정해줘야 함)
  # 파라미터: 모델을 통해서 추정할 수 있음.
grid_search=GridSearchCV(        
    estimator=eln_model, 
    param_grid=param_grid, # mse를 가장 낮게하는 파람 그리드를 알고싶어
    scoring='neg_mean_squared_error',
    cv=5
)
grid_search.fit(train_x, train_y) # 우리 데이터에 맞는 하이퍼파라미터
best_eln_model=grid_search.best_estimator_ # 최적의 파라미터 

# 그리드 서치 for RandomForests
param_grid={
    'max_depth': [3, 5, 7],
    'min_samples_split': [20, 10, 5],
    'min_samples_leaf': [5, 10, 20, 30],
    'max_features': ['sqrt', 'log2', None] # 변수들을 몇개 고려할건가. sqrt, log로  변수 개수 줄여줌. None은 변수 다 고려.
}
grid_search=GridSearchCV(
    estimator=rf_model,
    param_grid=param_grid,
    scoring='neg_mean_squared_error',
    cv=5
)
grid_search.fit(train_x, train_y) 
grid_search.best_params_
best_rf_model=grid_search.best_estimator_ # cv 다섯개 했을 때 mse가 제일 적게하는 알파, l1_ratio를 elastickNet 에 설정 해주겠다. -> best모델 두개 만들어놓음


# 스택킹
y1_hat=best_eln_model.predict(train_x) # eln모델로 예측한 y
y2_hat=best_rf_model.predict(train_x) # rf 모델로 예측한 y


train_x_stack=pd.DataFrame({
    'y1':y1_hat,
    'y2':y2_hat
}) # 모델에서 예측된 값들로 데이터프레임 만들어줌 

# 블렌더(릿지 외에 다른 걸 써도됨.)
from sklearn.linear_model import Ridge

rg_model = Ridge()
param_grid={
    'alpha': np.arange(0, 10, 0.01)
}
grid_search=GridSearchCV( #  mse 가장 작게하는 하이퍼 파라미터 구하기 위해 다시 그리드 서치함.
    estimator=rg_model,
    param_grid=param_grid,
    scoring='neg_mean_squared_error',
    cv=5
)
grid_search.fit(train_x_stack, train_y) 
grid_search.best_params_
blander_model=grid_search.best_estimator_ 
# 베스트 릿지 모델
blander_model.coef_
blander_model.intercept_

pred_y_eln=best_eln_model.predict(test_x)
pred_y_rf=best_rf_model.predict(test_x) 

test_x_stack=pd.DataFrame({
    'y1': pred_y_eln,
    'y2': pred_y_rf
}) # 실제 test_y 의 값으로 train_y가 잘 예측 되었는지 확인???

pred_y=blander_model.predict(test_x_stack)

# SalePrice 바꿔치기
sub_df["SalePrice"] = pred_y
sub_df

# # csv 파일로 내보내기
# sub_df.to_csv("./data/houseprice/sample_submission11.csv", index=False)
