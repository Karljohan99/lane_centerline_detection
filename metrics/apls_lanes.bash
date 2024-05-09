declare -a arr=(118 119 120 121 122 123 124 125 126 127 128 129)

# source directory
dir=RNGDet++_roi256_lanes/test

echo $dir
# now loop through the above array
for i in "${arr[@]}"   
do
    if test -f "../${dir}/graph/${i}.p"; then
        echo "========================$i======================"
        python ./apls/convert.py "../data/lanes256_large/dataset/region_${i}_graph_gt.pickle" gt.json
        python ./apls/convert.py "../${dir}/graph/${i}.p" prop.json
        go run ./apls/main.go gt.json prop.json ../$dir/results/apls/$i.txt 
    fi
done
python apls.py --dir $dir
