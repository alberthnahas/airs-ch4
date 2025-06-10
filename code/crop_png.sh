#!/bin/bash

mv monthly_idn_1.png oco2_co2mx_idn_01.png

### Reformat PNG files for final layout using ImageMagick
for i in 01
do
   composite -geometry 250x75+50+420 logo_bmkg.png oco2_co2mx_idn_$i.png oco2_co2mx_idn_comp_$i.png
   convert oco2_co2mx_idn_comp_$i.png -crop 790x550+0+55+10+0 +repage oco2_co2mx_idn_crop_$i.png
   rm oco2_co2mx_idn_comp_$i.png
   mv oco2_co2mx_idn_crop_$i.png oco2_co2mx_idn_$i.png
   mv  oco2_co2mx_idn_$i.png airs_ch4mx_idn_$i.png
done
