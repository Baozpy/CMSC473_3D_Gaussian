# Using Diffusion Models for Sparse 3D Gaussian Splatting





## Introduction

3D Gaussian Splatting [Kerbl et. al.](https://arxiv.org/abs/2308.04079) has quickly become a leading approach for real-time rendering by representing scenes as collections of anisotropic Gaussians with learnable geometric and appearance attributes, enabling high-quality view synthesis without the heavy volumetric integration required by implicit radiance fields [Mildenhall et. al.](https://arxiv.org/abs/2003.08934). However, despite its efficiency and strong performance under dense, well-covered input views, the method faces significant challenges when applied to a set of sparse input views common in mobile captures from the average user. With limited viewpoints, photometric and geometric cues become insufficiently constrained, leading to depth ambiguities, unstable optimization, floating artifacts, and overfitting to the few available views. These issues highlight an important gap between controlled experimental conditions and real-world data acquisition, motivating ongoing research into structural priors, depth cues, and hybrid representations that aim to make Gaussian Splatting more robust and reliable under sparse input.

## What We Accomplished

Our team conducted many experiments ///
