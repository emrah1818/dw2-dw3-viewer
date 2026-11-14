#include <fstream>
#include <iostream>
#include "dw2_model.hpp"
#include "dw2_anim.hpp"
int main(int argc,char**argv){std::ifstream model_file(argv[1],std::ios::binary);dw2_model model(model_file);std::ifstream animation_file(argv[2],std::ios::binary);dw2_anim anim(animation_file,model.objects.size(),'A');std::cout<<model.objects.size()<<" "<<anim.frames.size()<<"\n";for(auto &object:model.objects)std::cout<<object.vertices.size()<<" "<<object.normals.size()<<" "<<object.faces.size()<<"\n";for(auto &frame:anim.frames){std::cout<<frame.keyframe_indices.size()<<" "<<(int)frame.termination_mask<<" "<<frame.loop_mask<<"\n";}for(auto &keys:anim.keyframes){for(auto &mat:keys.transforms){for(int i=0;i<3;i++)for(int j=0;j<3;j++)std::cout<<mat.m[i][j]<<" ";for(int i=0;i<3;i++)std::cout<<mat.t[i]<<" ";std::cout<<"\n";}}}
