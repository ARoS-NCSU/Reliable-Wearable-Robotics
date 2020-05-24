# Environmental Context Prediction for Lower Limb Prostheses with Uncertainty Quantification (T-ASE 2020)

This is the example implementation for our [IEEE T-ASE paper]().

## Tested Environment 
- Ubuntu 16.04 LTS
- Python 3.7.5
- Tensorflow 1.14.0
- Keras 2.2.4
- OpenCV 4.1.1
- Scipy 1.2.1
- Numpy 1.17.3
- Sklearn 0.21.3


## Training & Testing
- Step One: Download dataset from the [paper homepage](https://research.ece.ncsu.edu/aros/paper-tase2020-lowerlimb/) and unzip the files. 
- Step Two: Run extract_pretrained_feature.py to extract and save image features (please change the corresponding data and feature directory). 
- Step Three: Run run_pipeline.py to train and evaluate terrain recognition and probability calibration networks (please change the corresponding data and feature directory). 
- Step Four: Run plot_reliability_diagram.m and plot_prediction_accuracy.m to visualize the reliability diagrams of the calibrated probability and the prediction accuracy comparison. 


## Citations
If you find our work useful in your research, please consider citing:
```
@ARTICLE{zhongEnv2020,
  author={B. {Zhong} and R. {Luiz da Silva} and M. {Li} and H. {Huang} and E. {Lobaton}},
  journal={IEEE Transactions on Automation Science and Engineering}, 
  title={Environmental Context Prediction for Lower Limb Prostheses With Uncertainty Quantification}, 
  year={2020},
  volume={},
  number={},
  pages={1-13},}
```
