declare -a arr=(470530 533474 584694 589547 582538 581694 581633 470658 470663 585541 586536 585693 539547 580635 585538 587542 587546 586541 588542 588737 589548 589715 589543 587737 471592)

# source directory
dir=RNGDet++_roads256_multi_ins/test

echo $dir
# now loop through the above array
for i in "${arr[@]}"   
do
    if test -f "../${dir}/graph/${i}.p"; then
        echo "========================$i======================"
        python ./apls/convert.py "../data/roads256/dataset/region_${i}_graph_gt.pickle" gt.json
        python ./apls/convert.py "../${dir}/graph/${i}.p" prop.json
        go run ./apls/main.go gt.json prop.json ../$dir/results/apls/$i.txt 
    fi
done
python apls.py --dir $dir
