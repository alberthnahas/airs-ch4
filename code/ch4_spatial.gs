reinit


****** set map area
*** setting background color and clearing the area	
*** gridlines are disabled
'set display white'
'clear'
'set grid off'
****** end mapping area


****** open file
*** preferred file is pre-processed file via CDO commands (https://code.mpimet.mpg.de/projects/cdo)
'sdfopen ch4_surface_202502.nc'
****** end opening file


****** set boundaries 
*** lat-lon given covers Indonesia
'set lon  90. 145.'
'set lat -15. 10.'
'set xlopts 1 2 0.10'
'set ylopts 1 2 0.10'
****** end setting boundaries


****** start while looping
*** reflects the timestep of the file
*** number of t should be adjusted accordingly
t = 1
while (t <= 1)


****** set color legend
'clear'
'set rgb  200  100  100  100 100'
'color 1850 2050 2 -kind cyan->lime->yellow->orange->red->crimson'
****** end setting map attributes


****** display CO2 mixing ratio and titles
'set t 't 
'set gxout shaded'
'set mpt 1 off'
'd ch4*1e9'
'q time'
  day = substr(result,11,2)
  month = substr(result,13,3)
  year = substr(result,16,4)
  time = substr(result,8,2)
** convert English to Indonesian spelling
 if (month="MAY"); month="MEI"; endif
 if (month="AUG"); month="AGT"; endif
 if (month="OCT"); month="OKT"; endif
 if (month="DEC"); month="DES"; endif
**       
'set strsiz 0.15'
'set string 1 r 2 0'
'draw string 10.5 7.2 'month' 'year
'set strsiz 0.17'
'set string 1 l 5 0'
'draw string 0.5 7.2 CH`b4 `n (ppb) pada level ~1000 hPa'
'set strsiz 0.11'
'set string 1 l 2 90'
'draw string 10.6 1.53 NASA/AIRS-AQUA'
** highlight regencies of interest
'set gxout shp'
'set line 1 1 1'
'set shpopts -1'
'draw shp Indonesia_38_Provinsi.shp'
'set shpopts 200'
'draw shp world_without_idn.shp'
**
****** end displaying CO2 mixing ratio and titles


****** set color bar
'set strsiz 0.12'
'color 1850 2050 2 -kind cyan->lime->yellow->orange->red->crimson -xcbar 0.5 10.5 0.75 0.95 -fs 10 -fh 0.1 -fw 0.1 -edge triangle'
*'xcbar 1. 10. 0.45 0.65 -fh 0.1 -fw 0.1 -ft 2 -levcol 0 400 3 402 10 404 16 406 17 408 18 410 19 412 20 414 21 416 22 418 23 420 9 -edge triangle -line on'   
****** end setting color bar


****** produce figures
'printim monthly_idn_'t'.png'
****** end producing figures


t = t + 1
endwhile
****** end while looping
