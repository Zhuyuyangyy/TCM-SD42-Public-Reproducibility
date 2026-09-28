# Reproducible figures for the TCM-SD42 manuscript.
# Requires base R only. Run from the repository root:
#   Rscript figures_r/reproduce_figures.R
# Outputs: results/figures_r/figure1_overall.png ... figure5_framework.png

args <- commandArgs(trailingOnly = TRUE)
root <- if (length(args)) args[[1]] else "."
data_dir <- file.path(root, "results")
out_dir <- file.path(data_dir, "figures_r")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

read_csv <- function(name) read.csv(file.path(data_dir, name), check.names = FALSE,
                                    stringsAsFactors = FALSE, fileEncoding = "UTF-8")
perf <- read_csv("clean4218_seed42.csv")
seed <- read_csv("three_seed_summary.csv")
acc_pairs <- read_csv("pairwise_significance_seed42.csv")
macro_pairs <- read_csv("pairwise_macro_f1_bootstrap_seed42.csv")
ba_pairs <- read_csv("pairwise_balanced_accuracy_bootstrap_seed42.csv")

# Fail closed if the publication-critical values drift from the frozen tables.
expected <- c(zybert = .7577, internlm3 = .6958, macbert = .6278, qwen3 = .5870)
actual <- setNames(perf[["syn_acc@1"]], perf$model)
stopifnot(all(names(expected) %in% names(actual)),
          max(abs(actual[names(expected)] - expected)) < 1e-10,
          nrow(acc_pairs) == 6L, nrow(macro_pairs) == 6L, nrow(ba_pairs) == 6L)

cols <- c("ZY-BERT" = "#1769AA", "InternLM3-8B" = "#E69F00",
          "MacBERT" = "#009E73", "Qwen3-8B" = "#CC79A7")
short <- c(zybert="ZY-BERT", internlm3="InternLM3-8B", macbert="MacBERT", qwen3="Qwen3-8B")
model_order <- c("ZY-BERT", "InternLM3-8B", "MacBERT", "Qwen3-8B")
clean_theme <- function() {
  par(family="sans", col.axis="#263238", col.lab="#263238", col.main="#172B4D",
      fg="#52616B", las=1, bty="n", tcl=-.22, mgp=c(2.2,.65,0),
      mar=c(4.2,4.5,2.5,1.1), xaxs="i", yaxs="i")
}
open_png <- function(name, width=3600, height=2200) {
  grDevices::png(file.path(out_dir,name), width=width, height=height, res=300,
                 pointsize=11, bg="white")
}

# Figure 1: seed-42 metrics and paired effects.
open_png("figure1_overall.png", 4200, 2200)
layout(matrix(c(1,2,3),1,3), widths=c(1.02,1.08,1.34))
clean_theme(); par(mar=c(4.1,4.9,2.4,.5))
d <- perf[match(c("zybert","internlm3","macbert","qwen3"), perf$model),]
y <- rev(seq_len(nrow(d)))
plot(d[["syn_acc@1"]]*100,y,xlim=c(52,81),ylim=c(.45,4.55),type="n",yaxt="n",
     xlab="Accuracy (%)",ylab="",main="A  Accuracy with 95% CI")
axis(2,at=y,labels=model_order,las=1,tick=FALSE,cex.axis=.9)
segments(d$ci_lower*100,y,d$ci_upper*100,y,col=cols[model_order],lwd=2.5)
points(d[["syn_acc@1"]]*100,y,pch=21,bg=cols[model_order],col="white",cex=1.25,lwd=1)
text(d$ci_upper*100+.8,y,sprintf("%.2f",d[["syn_acc@1"]]*100),adj=0,cex=.8,col="#263238")
grid(nx=NA,ny=NULL,col="#E8EDF1",lty=1); box(col="#CFD8DC")
clean_theme(); par(mar=c(4.1,1.1,2.4,1.3))
metric_mat <- t(as.matrix(d[,c("macro_f1","weighted_f1","balanced_accuracy")]))*100
colnames(metric_mat) <- model_order
plot(range(50,82),c(.45,4.55),type="n",yaxt="n",xlab="Performance (%)",ylab="",
     main="B  Class-sensitive metrics")
for (j in seq_along(model_order)) {
  yy <- 4.1-j
  points(metric_mat[1,j],yy,pch=16,col=cols[model_order[j]],cex=1.15)
  points(metric_mat[2,j],yy,pch=15,col=cols[model_order[j]],cex=1.15)
  points(metric_mat[3,j],yy,pch=17,col=cols[model_order[j]],cex=1.15)
}
legend("bottomright",legend=c("Macro-F1","Weighted-F1","Balanced accuracy"),
       pch=c(16,15,17),pt.cex=.9,col="#3C4858",bty="n",cex=.78)
grid(nx=NULL,ny=NA,col="#E8EDF1",lty=1); box(col="#CFD8DC")
clean_theme(); par(mar=c(4.1,5.7,2.4,1.3))
lab <- paste(acc_pairs$model_a,"vs",acc_pairs$model_b)
ord <- rev(seq_len(nrow(acc_pairs)))
plot(acc_pairs$delta_accuracy_pp[ord],seq_along(ord),xlim=c(0,20),ylim=c(.4,6.6),
     type="n",yaxt="n",xlab="Accuracy difference (percentage points)",ylab="",
     main="C  Paired effect sizes")
axis(2,at=seq_along(ord),labels=lab[ord],las=1,tick=FALSE,cex.axis=.77)
abline(v=0,col="#7C8A96",lty=2)
segments(acc_pairs$ci95_lower_pp[ord],seq_along(ord),acc_pairs$ci95_upper_pp[ord],seq_along(ord),
         col="#1769AA",lwd=2)
points(acc_pairs$delta_accuracy_pp[ord],seq_along(ord),pch=21,bg="#1769AA",col="white",cex=1.1)
text(acc_pairs$ci95_upper_pp[ord]+.35,seq_along(ord),
     sprintf("+%.2f",acc_pairs$delta_accuracy_pp[ord]),adj=0,cex=.72)
grid(nx=NA,ny=NULL,col="#E8EDF1",lty=1); box(col="#CFD8DC")
dev.off()

# Figure 2: per-seed values and mean +/- sample SD for both newly trained systems.
open_png("figure2_seed_robustness.png", 3600, 3000)
metrics <- c("accuracy","macro_f1","weighted_f1","balanced_accuracy")
metric_names <- c("Accuracy (%)","Macro-F1 (%)","Weighted-F1 (%)","Balanced accuracy (%)")
layout(matrix(1:4,2,2,byrow=TRUE))
for (k in seq_along(metrics)) {
  clean_theme(); par(mar=c(3.7,4.1,2.6,.8))
  nm <- metrics[k]; sm <- seed[seed$metric==nm,]
  yy <- c(2,1); xmean <- sm$mean_percent[match(c("ZY-BERT","InternLM3-8B"),sm$model)]
  xsd <- sm$sd_percent[match(c("ZY-BERT","InternLM3-8B"),sm$model)]
  plot(c(min(xmean-xsd)-1,max(xmean+xsd)+1),c(.5,2.5),type="n",yaxt="n",
       xlab=metric_names[k],ylab="",main=paste(LETTERS[k],metric_names[k]))
  axis(2,at=yy,labels=c("ZY-BERT","InternLM3-8B"),tick=FALSE)
  for (j in 1:2) {
    rr <- perf[match(c("zybert","internlm3")[j],perf$model),]
    vals <- c(if(j==1) c(75.77,75.34,73.64) else c(69.58,69.49,69.18))
    # Frozen per-seed metric values are explicitly listed in the supplementary provenance tables.
    if (nm=="macro_f1") vals <- if(j==1)c(66.51,66.37,65.31) else c(60.74,61.24,60.68)
    if (nm=="weighted_f1") vals <- if(j==1)c(78.00,77.59,75.93) else c(72.20,72.24,72.03)
    if (nm=="balanced_accuracy") vals <- if(j==1)c(79.32,79.53,77.59) else c(73.55,74.27,73.62)
    offsets <- c(.12,0,-.12)
    points(vals,rep(yy[j],3)+offsets,pch=c(21,22,17),bg=cols[c("ZY-BERT","InternLM3-8B")[j]],
           col="white",cex=1.1)
    segments(xmean[j]-xsd[j],yy[j]-.22,xmean[j]+xsd[j],yy[j]-.22,col="#202A35",lwd=1.8)
    points(xmean[j],yy[j]-.22,pch=23,bg="#202A35",col="white",cex=1.05)
    text(xmean[j]+xsd[j]+.18,yy[j]-.22,sprintf("%.2f +/- %.2f",xmean[j],xsd[j]),
         adj=0,cex=.72,col="#263238")
  }
  legend("bottomright",legend=c("Seed 42","Seed 2026","Seed 7","Mean +/- SD"),
         pch=c(21,22,17,23),pt.bg=c("#1769AA","#E69F00","#009E73","#202A35"),
         col="white",bty="n",cex=.7,ncol=2)
  grid(nx=NA,ny=NULL,col="#E8EDF1",lty=1); box(col="#CFD8DC")
}
dev.off()

# Figure 3: recurrent errors are read directly from the four frozen confusion matrices.
model_files <- c(zybert="confusion_matrix_zybert.csv",internlm3="confusion_matrix_internlm3.csv",
                 macbert="confusion_matrix_macbert.csv",qwen3="confusion_matrix_qwen3.csv")
models3 <- c("ZY-BERT","InternLM3-8B","MacBERT","Qwen3-8B")
get_error <- function(gold, predicted) {
  vapply(model_files,function(f) {
    cm <- read.csv(file.path(data_dir,f),check.names=FALSE,row.names=1,fileEncoding="UTF-8")
    as.numeric(cm[gold,predicted])
  },numeric(1))
}
err_a <- get_error("气滞血瘀","肝肾亏虚")
err_b <- get_error("正虚瘀结","正虚毒瘀")
stopifnot(identical(as.numeric(err_a),c(77,92,87,84)),identical(as.numeric(err_b),c(49,49,72,43)))
open_png("figure3_confusion_and_validity.png", 4200, 2200)
layout(matrix(1:3,1,3),widths=c(1.05,1.05,.78))
bar_panel <- function(values, title, xlim) {
  clean_theme(); par(mar=c(4.1,5.3,3.0,.5))
  yy <- rev(seq_along(values))
  plot(values,yy,xlim=xlim,ylim=c(.5,4.55),type="n",yaxt="n",xlab="Number of seed-42 errors",
       ylab="",main=title)
  axis(2,at=yy,labels=models3,las=1,tick=FALSE,cex.axis=.82)
  segments(0,yy,values,yy,col=cols[models3],lwd=9)
  text(values+max(xlim)*.025,yy,labels=values,adj=0,cex=.83)
  grid(nx=NA,ny=NULL,col="#E8EDF1",lty=1); box(col="#CFD8DC")
}
bar_panel(err_a,"A  Qi stagnation and blood stasis to\nliver-kidney deficiency",c(0,110))
bar_panel(err_b,"B  Healthy-qi deficiency with stasis to\nhealthy-qi deficiency with toxin and stasis",c(0,85))
clean_theme(); par(mar=c(4.1,2.5,3.0,1.0))
empty <- perf$empty_pred_rate[match(c("zybert","internlm3","macbert","qwen3"),perf$model)]*100
plot(empty,rev(1:4),xlim=c(0,.075),ylim=c(.5,4.55),type="n",yaxt="n",xlab="Empty predictions (%)",
     ylab="",main="C  Output reliability")
axis(2,at=rev(1:4),labels=models3,las=1,tick=FALSE,cex.axis=.77)
segments(0,rev(1:4),empty,rev(1:4),col=cols[models3],lwd=9)
text(empty+.003,rev(1:4),labels=sprintf("%.2f",empty),adj=0,cex=.8)
grid(nx=NA,ny=NULL,col="#E8EDF1",lty=1); box(col="#CFD8DC")
dev.off()

# Shared box-and-arrow drawing helpers for the two protocol schematics.
box_node <- function(x,y,w,h,title,body,fill="#F7FAFC",border="#52616B",cex=.72) {
  rect(x-w/2,y-h/2,x+w/2,y+h/2,col=fill,border=border,lwd=1.25)
  text(x,y+h*.20,title,font=2,cex=cex,col="#172B4D")
  text(x,y-h*.12,body,cex=cex*.82,col="#263238",xpd=NA)
}
arrow <- function(x1,y1,x2,y2) arrows(x1,y1,x2,y2,length=.09,angle=22,col="#52616B",lwd=1.15)

# Figure 4: dataset and analysis workflow.
open_png("figure4_workflow.png", 4200, 2200)
par(mar=c(.4,.5,2.4,.5),xaxs="i",yaxs="i")
plot(0:1,0:1,type="n",axes=FALSE,xlab="",ylab="",main="Controlled benchmark workflow",cex.main=1.15)
xs <- c(.12,.37,.62,.87); yy <- .70; w <- .205; h <- .33
box_node(xs[1],yy,w,h,"A  Data provenance","Public TCM-SD corpus\n54,152 records; source\n148 normalized labels",cex=.75)
box_node(xs[2],yy,w,h,"B  Frozen 42-class task","278 source labels\n42 met historical support\nthresholds in all splits",cex=.75)
box_node(xs[3],yy,w,h,"C  Leakage control","4,452 source test cases\n234 exact/near duplicates\nremoved; N = 4,218",cex=.75)
box_node(xs[4],yy,w,h,"D  Matched comparison","MacBERT, ZY-BERT, Qwen3,\nInternLM3; fixed label order\nand identical test records",cex=.75)
for(i in 1:3) arrow(xs[i]+w/2,yy,xs[i+1]-w/2,yy)
xs2 <- c(.22,.50,.78); y2 <- .25
box_node(xs2[1],y2,.235,.31,"E  Performance metrics","Accuracy, macro-F1,\nweighted-F1, balanced\naccuracy",cex=.78)
box_node(xs2[2],y2,.235,.31,"F  Paired inference","2,000 paired bootstrap\nresamples; exact McNemar;\nHolm correction",cex=.78)
box_node(xs2[3],y2,.235,.31,"G  Robustness and audit","Three seeds for two systems;\nclass-stratified sensitivity;\ntaxonomy-overlap audit",cex=.78)
arrow(xs[4],yy-h/2,xs2[2],y2+.31/2)
arrow(xs2[2]-.06,y2+.31/2,xs2[1]+.10,y2+.31/2)
arrow(xs2[2]+.06,y2+.31/2,xs2[3]-.10,y2+.31/2)
dev.off()

# Figure 5: model branches and common frozen evaluation.
open_png("figure5_framework.png", 4200, 2500)
par(mar=c(.3,.5,2.4,.5),xaxs="i",yaxs="i")
plot(0:1,0:1,type="n",axes=FALSE,xlab="",ylab="",main="System adaptation and unified evaluation framework",cex.main=1.1)
node_x <- c(.10,.29,.49,.69,.89); yy1 <- .78; bw <- .16; bh <- .19
nodes <- list(
 c("Clinical input","Disease name + chief complaint\nFour diagnostic information\ncurrent illness summary"),
 c("Tokenizer","Fixed tokenizer\nMax length = 512"),
 c("Encoder","MacBERT\nor\nZY-BERT"),
 c("Classifier","42-way head"),
 c("Output","One\nlabel"))
for(i in seq_along(node_x)) box_node(node_x[i],yy1,bw,bh,nodes[[i]][1],nodes[[i]][2],cex=.73)
for(i in 1:4) arrow(node_x[i]+bw/2,yy1,node_x[i+1]-bw/2,yy1)
node_x2 <- c(.10,.29,.49,.69,.89); yy2 <- .50
nodes2 <- list(c("Clinical input","Same frozen input_text"),c("Generative model","Qwen3-8B\nor\nInternLM3-8B-Instruct"),
 c("Task adaptation","4-bit NF4 QLoRA\nLoRA r=16, alpha=32\nclosed-label SFT"),
 c("Generation","Label + short\nrationale"),c("Parser","Frozen\n42-label parser"))
for(i in seq_along(node_x2)) box_node(node_x2[i],yy2,bw,bh,nodes2[[i]][1],nodes2[[i]][2],fill="#FFF9EF",cex=.68)
for(i in 1:4) arrow(node_x2[i]+bw/2,yy2,node_x2[i+1]-bw/2,yy2)
text(.015,yy1,"A",font=2,cex=1.1,adj=0); text(.015,yy2,"B",font=2,cex=1.1,adj=0)
text(.015,.19,"C",font=2,cex=1.1,adj=0)
arrow(.89,.39,.89,.30)
low_x <- c(.13,.315,.50,.685,.87); low_w <- c(.17,.17,.17,.17,.17); low_h <- .16
low_nodes <- list(c("Clean test set","N = 4,218\nfixed case IDs"),c("Unified label space","Frozen 42-class\nlabel order"),
 c("Performance","Accuracy + Macro-F1\nWeighted-F1 +\nBalanced accuracy"),
 c("Paired inference","Bootstrap CIs\nMcNemar + Holm"),c("Robustness","3 seeds for\nZY-BERT and\nInternLM3"))
for(i in seq_along(low_x)) box_node(low_x[i],.22,low_w[i],low_h,low_nodes[[i]][1],low_nodes[[i]][2],fill="#F0F6FA",cex=.67)
for(i in 1:4) arrow(low_x[i]+low_w[i]/2,.22,low_x[i+1]-low_w[i+1]/2,.22)
dev.off()

cat("Created five deterministic base-R figures in ", normalizePath(out_dir), "\n", sep="")
